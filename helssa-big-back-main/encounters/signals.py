from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    Encounter, AudioChunk, Transcript,
    SOAPReport, Prescription
)
from .tasks import (
    process_audio_chunk_stt,
    process_encounter_audio_complete,
    notify_doctor_soap_ready,
    notify_patient_summary_ready
)


@receiver(post_save, sender=Encounter)
def handle_encounter_post_save(sender, instance, created, **kwargs):
    """پس از ذخیره ملاقات"""
    
    if created:
        # ایجاد کد دسترسی برای ملاقات‌های جدید
        if not instance.access_code:
            from .utils.generators import generate_access_code
            instance.access_code = generate_access_code()
            instance.save(update_fields=['access_code'])
            
    else:
        # بررسی تغییر وضعیت
        if instance.status == 'completed' and instance.ended_at:
            # شروع پردازش‌های پس از اتمام ویزیت
            process_encounter_audio_complete.apply_async(
                args=[str(instance.id)],
                countdown=60  # 1 دقیقه تاخیر
            )


@receiver(post_save, sender=AudioChunk)
def handle_audio_chunk_post_save(sender, instance, created, **kwargs):
    """پس از ذخیره قطعه صوتی"""
    
    if created and instance.is_ready_for_transcription:
        # شروع پردازش STT
        process_audio_chunk_stt.delay(str(instance.id))


@receiver(post_save, sender=Transcript)
def handle_transcript_post_save(sender, instance, created, **kwargs):
    """پس از ذخیره رونویسی"""
    
    if created:
        # بررسی تکمیل بودن همه رونویسی‌ها
        encounter = instance.audio_chunk.encounter
        total_chunks = encounter.audio_chunks.count()
        transcribed_chunks = Transcript.objects.filter(
            audio_chunk__encounter=encounter
        ).count()
        
        if total_chunks > 0 and total_chunks == transcribed_chunks:
            # همه قطعات رونویسی شده‌اند
            from .tasks import merge_encounter_transcripts
            merge_encounter_transcripts.delay(str(encounter.id))


@receiver(post_save, sender=SOAPReport)
def handle_soap_report_post_save(sender, instance, created, **kwargs):
    """پس از ذخیره گزارش SOAP"""
    
    if created:
        # اطلاع به پزشک
        notify_doctor_soap_ready.delay(
            str(instance.encounter.id),
            str(instance.id)
        )
        
    else:
        # بررسی تغییر وضعیت
        if instance.patient_shared and 'patient_shared_at' in kwargs.get('update_fields', []):
            # گزارش با بیمار به اشتراک گذاشته شد
            notify_patient_summary_ready.delay(str(instance.encounter.id))


@receiver(pre_save, sender=Prescription)
def handle_prescription_pre_save(sender, instance, **kwargs):
    """قبل از ذخیره نسخه"""
    
    if not instance.pk:  # نسخه جدید
        # تولید شماره نسخه
        if not instance.prescription_number:
            from .utils.generators import generate_prescription_number
            instance.prescription_number = generate_prescription_number()
            
        # تنظیم تاریخ انقضا
        if not instance.expires_at:
            instance.expires_at = timezone.now() + timezone.timedelta(days=180)
            
    else:
        # بررسی تغییر وضعیت
        if instance.status == 'issued' and not instance.is_signed:
            # نسخه صادر شده اما امضا نشده
            # TODO: تولید امضای دیجیتال
            pass


@receiver(post_save, sender=Prescription)
def handle_prescription_post_save(sender, instance, created, **kwargs):
    """پس از ذخیره نسخه"""
    
    if not created and instance.status == 'dispensed':
        # نسخه تحویل داده شد
        # TODO: ارسال نوتیفیکیشن به بیمار
        pass


@receiver(post_delete, sender=AudioChunk)
def handle_audio_chunk_delete(sender, instance, **kwargs):
    """پس از حذف قطعه صوتی"""
    
    # حذف فایل از storage
    if instance.file_url:
        # TODO: حذف از MinIO
        pass


@receiver(post_delete, sender=EncounterFile)
def handle_encounter_file_delete(sender, instance, **kwargs):
    """پس از حذف فایل ملاقات"""
    
    # حذف فایل از storage
    if instance.file_url:
        # TODO: حذف از MinIO
        pass


# Signal برای تنظیم خودکار prescription در SOAP report
@receiver(post_save, sender=Prescription)
def update_soap_medications(sender, instance, created, **kwargs):
    """به‌روزرسانی داروهای SOAP هنگام تغییر نسخه"""
    
    try:
        soap_report = instance.encounter.soap_report
        
        # به‌روزرسانی لیست داروها در SOAP
        all_medications = []
        for prescription in instance.encounter.prescriptions.filter(status='issued'):
            all_medications.extend(prescription.medications)
            
        soap_report.medications = all_medications
        soap_report.save(update_fields=['medications'])
        
    except SOAPReport.DoesNotExist:
        # هنوز گزارش SOAP ایجاد نشده
        pass