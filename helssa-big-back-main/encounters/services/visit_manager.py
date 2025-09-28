from datetime import datetime, timedelta
from typing import Dict, List, Optional
from django.utils import timezone
from django.db.models import F, Q
from asgiref.sync import sync_to_async

from ..models import Encounter
from .video_service import VideoConferenceService
from ..utils.encryption import generate_encryption_key


class SchedulingConflictError(Exception):
    """خطای تداخل زمان‌بندی"""
    pass


class EarlyStartError(Exception):
    """خطای شروع زودهنگام ویزیت"""
    pass


class VisitSchedulingService:
    """سرویس زمان‌بندی ویزیت‌ها"""
    
    def __init__(self):
        self.video_service = VideoConferenceService()
        
    async def schedule_visit(
        self,
        patient_id: str,
        doctor_id: str,
        visit_type: str,
        scheduled_at: datetime,
        duration_minutes: int = 30,
        chief_complaint: str = "",
        notes: Optional[str] = None
    ) -> Encounter:
        """زمان‌بندی ویزیت جدید"""
        
        # بررسی در دسترس بودن پزشک
        if not await self._check_doctor_availability(
            doctor_id, scheduled_at, duration_minutes
        ):
            raise SchedulingConflictError(
                "پزشک در این زمان در دسترس نیست"
            )
            
        # بررسی تداخل با ویزیت‌های بیمار
        if await self._has_patient_conflict(
            patient_id, scheduled_at, duration_minutes
        ):
            raise SchedulingConflictError(
                "شما در این زمان ویزیت دیگری دارید"
            )
            
        # محاسبه هزینه ویزیت
        fee_amount = await self._calculate_visit_fee(
            doctor_id, visit_type, duration_minutes
        )
        
        # ایجاد encounter
        encounter = await sync_to_async(Encounter.objects.create)(
            patient_id=patient_id,
            doctor_id=doctor_id,
            type=visit_type,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            chief_complaint=chief_complaint,
            patient_notes=notes,
            fee_amount=fee_amount,
            encryption_key=generate_encryption_key()
        )
        
        # ایجاد اتاق ویدیو برای ویزیت‌های آنلاین
        if visit_type in ['video', 'audio']:
            video_room = await self.video_service.create_room(
                encounter_id=str(encounter.id),
                scheduled_at=scheduled_at,
                duration_minutes=duration_minutes
            )
            
            encounter.video_room_id = video_room['room_id']
            encounter.patient_join_url = video_room['patient_url']
            encounter.doctor_join_url = video_room['doctor_url']
            await sync_to_async(encounter.save)()
            
        # ارسال نوتیفیکیشن
        await self._send_scheduling_notifications(encounter)
        
        # تنظیم یادآوری‌ها
        await self._schedule_reminders(encounter)
        
        return encounter
        
    async def confirm_visit(
        self,
        encounter_id: str,
        confirmed_by: str
    ) -> Encounter:
        """تایید ویزیت"""
        
        encounter = await sync_to_async(Encounter.objects.get)(
            id=encounter_id,
            status='scheduled'
        )
        
        # پردازش پرداخت
        if not encounter.is_paid:
            # TODO: اتصال به سرویس پرداخت
            encounter.is_paid = True
            
        # به‌روزرسانی وضعیت
        encounter.status = 'confirmed'
        encounter.metadata['confirmed_by'] = confirmed_by
        encounter.metadata['confirmed_at'] = datetime.utcnow().isoformat()
        await sync_to_async(encounter.save)()
        
        # ارسال تاییدیه
        await self._send_confirmation_notifications(encounter)
        
        return encounter
        
    async def start_visit(
        self,
        encounter_id: str,
        started_by: str
    ) -> Dict:
        """شروع ویزیت"""
        
        encounter = await sync_to_async(Encounter.objects.get)(
            id=encounter_id,
            status='confirmed'
        )
        
        # بررسی زمان
        now = timezone.now()
        scheduled_time = encounter.scheduled_at
        
        # اجازه شروع از 10 دقیقه قبل
        if now < scheduled_time - timedelta(minutes=10):
            raise EarlyStartError(
                f"ویزیت از {scheduled_time} قابل شروع است"
            )
            
        # به‌روزرسانی وضعیت
        encounter.status = 'in_progress'
        encounter.started_at = now
        await sync_to_async(encounter.save)()
        
        # شروع ضبط در صورت رضایت
        if encounter.recording_consent:
            await self._start_recording(encounter)
            
        # بازگشت اطلاعات اتصال
        return {
            'encounter_id': str(encounter.id),
            'video_room_id': encounter.video_room_id,
            'join_url': (
                encounter.doctor_join_url 
                if started_by == str(encounter.doctor_id)
                else encounter.patient_join_url
            ),
            'recording_enabled': encounter.is_recording_enabled,
            'estimated_end_time': now + timedelta(
                minutes=encounter.duration_minutes
            )
        }
        
    async def end_visit(
        self,
        encounter_id: str,
        ended_by: str
    ) -> Encounter:
        """پایان ویزیت"""
        
        encounter = await sync_to_async(Encounter.objects.get)(
            id=encounter_id,
            status='in_progress'
        )
        
        # به‌روزرسانی وضعیت
        encounter.status = 'completed'
        encounter.ended_at = timezone.now()
        await sync_to_async(encounter.save)()
        
        # توقف ضبط
        if encounter.is_recording_enabled:
            recording_url = await self._stop_recording(encounter)
            encounter.recording_url = recording_url
            await sync_to_async(encounter.save)()
            
        # شروع پردازش‌های پس از ویزیت
        await self._post_visit_processing(encounter)
        
        return encounter
        
    async def cancel_visit(
        self,
        encounter_id: str,
        cancelled_by: str,
        reason: str = ""
    ) -> Encounter:
        """لغو ویزیت"""
        
        encounter = await sync_to_async(Encounter.objects.get)(
            id=encounter_id,
            status__in=['scheduled', 'confirmed']
        )
        
        # به‌روزرسانی وضعیت
        encounter.status = 'cancelled'
        encounter.metadata['cancelled_by'] = cancelled_by
        encounter.metadata['cancelled_at'] = datetime.utcnow().isoformat()
        encounter.metadata['cancellation_reason'] = reason
        await sync_to_async(encounter.save)()
        
        # ارسال اطلاع‌رسانی
        await self._send_cancellation_notifications(encounter)
        
        # بازگشت وجه در صورت نیاز
        if encounter.is_paid:
            await self._process_refund(encounter)
            
        return encounter
        
    async def _check_doctor_availability(
        self,
        doctor_id: str,
        scheduled_at: datetime,
        duration_minutes: int
    ) -> bool:
        """بررسی در دسترس بودن پزشک"""
        
        # TODO: بررسی ساعات کاری پزشک از DoctorProfile
        
        # بررسی تداخل با ویزیت‌های دیگر
        end_time = scheduled_at + timedelta(minutes=duration_minutes)
        
        conflicts = await sync_to_async(
            Encounter.objects.filter(
                doctor_id=doctor_id,
                status__in=['scheduled', 'confirmed'],
                scheduled_at__lt=end_time,
                scheduled_at__gte=scheduled_at - timedelta(
                    minutes=F('duration_minutes')
                )
            ).exists
        )()
        
        return not conflicts
        
    async def _has_patient_conflict(
        self,
        patient_id: str,
        scheduled_at: datetime,
        duration_minutes: int
    ) -> bool:
        """بررسی تداخل با ویزیت‌های بیمار"""
        
        end_time = scheduled_at + timedelta(minutes=duration_minutes)
        
        conflicts = await sync_to_async(
            Encounter.objects.filter(
                patient_id=patient_id,
                status__in=['scheduled', 'confirmed'],
                scheduled_at__lt=end_time,
                scheduled_at__gte=scheduled_at - timedelta(
                    minutes=F('duration_minutes')
                )
            ).exists
        )()
        
        return conflicts
        
    async def _calculate_visit_fee(
        self,
        doctor_id: str,
        visit_type: str,
        duration_minutes: int
    ) -> float:
        """محاسبه هزینه ویزیت"""
        
        # TODO: دریافت تعرفه پزشک از DoctorProfile
        
        # تعرفه پیش‌فرض
        base_rates = {
            'in_person': 500000,  # 500 هزار تومان
            'video': 400000,      # 400 هزار تومان
            'audio': 300000,      # 300 هزار تومان
            'chat': 200000,       # 200 هزار تومان
            'follow_up': 250000,  # 250 هزار تومان
        }
        
        base_fee = base_rates.get(visit_type, 400000)
        
        # محاسبه بر اساس مدت زمان
        # هر 15 دقیقه اضافی، 25% افزایش
        extra_time = max(0, duration_minutes - 30)
        extra_fee = (extra_time / 15) * (base_fee * 0.25)
        
        return base_fee + extra_fee
        
    async def _send_scheduling_notifications(self, encounter: Encounter):
        """ارسال نوتیفیکیشن زمان‌بندی"""
        # TODO: اتصال به سرویس نوتیفیکیشن
        pass
        
    async def _send_confirmation_notifications(self, encounter: Encounter):
        """ارسال نوتیفیکیشن تایید"""
        # TODO: اتصال به سرویس نوتیفیکیشن
        pass
        
    async def _send_cancellation_notifications(self, encounter: Encounter):
        """ارسال نوتیفیکیشن لغو"""
        # TODO: اتصال به سرویس نوتیفیکیشن
        pass
        
    async def _schedule_reminders(self, encounter: Encounter):
        """تنظیم یادآوری‌ها"""
        # TODO: اتصال به سرویس scheduler
        pass
        
    async def _start_recording(self, encounter: Encounter):
        """شروع ضبط ویزیت"""
        if encounter.video_room_id:
            await self.video_service.start_recording(
                encounter.video_room_id,
                str(encounter.id)
            )
            
    async def _stop_recording(self, encounter: Encounter) -> Optional[str]:
        """توقف ضبط ویزیت"""
        if encounter.video_room_id:
            return await self.video_service.stop_recording(
                encounter.video_room_id,
                str(encounter.id)
            )
        return None
        
    async def _post_visit_processing(self, encounter: Encounter):
        """پردازش‌های پس از اتمام ویزیت"""
        # TODO: شروع پردازش STT و تولید SOAP
        pass
        
    async def _process_refund(self, encounter: Encounter):
        """پردازش بازگشت وجه"""
        # TODO: اتصال به سرویس پرداخت
        pass