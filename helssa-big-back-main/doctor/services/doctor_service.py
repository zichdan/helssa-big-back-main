"""
سرویس‌های مدیریت پزشک
Doctor Management Services
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, time
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q, Avg, Count
from django.utils import timezone

from ..models import (
    DoctorProfile, 
    DoctorSchedule, 
    DoctorShift, 
    DoctorCertificate,
    DoctorRating,
    DoctorSettings
)
from ..cores.orchestrator import DoctorCentralOrchestrator

User = get_user_model()
logger = logging.getLogger(__name__)


class DoctorProfileService:
    """
    سرویس مدیریت پروفایل پزشک
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.orchestrator = DoctorCentralOrchestrator()
    
    def create_doctor_profile(self, user: User, profile_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد پروفایل پزشک
        
        Args:
            user: کاربر پزشک
            profile_data: داده‌های پروفایل
            
        Returns:
            (success, result_data or error_info)
        """
        try:
            # بررسی وجود پروفایل قبلی
            if hasattr(user, 'doctor_profile'):
                return False, {'error': 'پروفایل پزشک قبلاً ایجاد شده است'}
            
            # اجرای workflow ایجاد پروفایل
            result = self.orchestrator.execute_doctor_workflow(
                'create_doctor_profile',
                profile_data,
                user
            )
            
            if result.status.value == 'completed':
                profile = result.data.get('create_profile', {}).get('profile')
                return True, {
                    'profile_id': str(profile.id),
                    'message': 'پروفایل پزشک با موفقیت ایجاد شد',
                    'profile': profile
                }
            else:
                return False, {
                    'error': 'خطا در ایجاد پروفایل',
                    'details': result.errors
                }
                
        except Exception as e:
            self.logger.error(f"Error creating doctor profile: {str(e)}")
            return False, {'error': 'خطای داخلی سرور', 'details': str(e)}
    
    def update_doctor_profile(self, user: User, profile_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        بروزرسانی پروفایل پزشک
        
        Args:
            user: کاربر پزشک
            profile_data: داده‌های جدید پروفایل
            
        Returns:
            (success, result_data or error_info)
        """
        try:
            if not hasattr(user, 'doctor_profile'):
                return False, {'error': 'پروفایل پزشک یافت نشد'}
            
            profile = user.doctor_profile
            
            # فیلدهای قابل ویرایش
            editable_fields = [
                'first_name', 'last_name', 'phone_number', 'clinic_address',
                'clinic_phone', 'biography', 'years_of_experience', 'profile_picture',
                'visit_duration', 'visit_price', 'auto_accept_appointments', 'allow_online_visits'
            ]
            
            # بروزرسانی فیلدها
            for field in editable_fields:
                if field in profile_data:
                    setattr(profile, field, profile_data[field])
            
            profile.save()
            
            self.logger.info(f"Doctor profile updated for user {user.id}")
            
            return True, {
                'profile_id': str(profile.id),
                'message': 'پروفایل با موفقیت بروزرسانی شد'
            }
            
        except ValidationError as e:
            return False, {'error': 'خطای اعتبارسنجی', 'details': str(e)}
        except Exception as e:
            self.logger.error(f"Error updating doctor profile: {str(e)}")
            return False, {'error': 'خطای داخلی سرور', 'details': str(e)}
    
    def get_doctor_profile(self, user: User) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت پروفایل پزشک
        
        Args:
            user: کاربر پزشک
            
        Returns:
            (success, profile_data or error_info)
        """
        try:
            if not hasattr(user, 'doctor_profile'):
                return False, {'error': 'پروفایل پزشک یافت نشد'}
            
            profile = user.doctor_profile
            
            return True, {
                'profile': profile,
                'verification_status': profile.is_verified,
                'rating_info': {
                    'rating': profile.rating,
                    'total_reviews': profile.total_reviews
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting doctor profile: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}
    
    def search_doctors(self, search_params: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        جستجوی پزشکان
        
        Args:
            search_params: پارامترهای جستجو
            
        Returns:
            (success, search_results or error_info)
        """
        try:
            queryset = DoctorProfile.objects.filter(is_active=True)
            
            # فیلتر بر اساس تخصص
            if search_params.get('specialty'):
                queryset = queryset.filter(specialty=search_params['specialty'])
            
            # فیلتر بر اساس تایید شدن
            if search_params.get('verified_only'):
                queryset = queryset.filter(is_verified=True)
            
            # فیلتر بر اساس ویزیت آنلاین
            if search_params.get('online_visit'):
                queryset = queryset.filter(allow_online_visits=True)
            
            # فیلتر بر اساس حداقل امتیاز
            if search_params.get('min_rating'):
                queryset = queryset.filter(rating__gte=search_params['min_rating'])
            
            # جستجوی نام
            if search_params.get('name'):
                name = search_params['name']
                queryset = queryset.filter(
                    Q(first_name__icontains=name) | 
                    Q(last_name__icontains=name)
                )
            
            # جستجوی مکان
            if search_params.get('location'):
                location = search_params['location']
                queryset = queryset.filter(clinic_address__icontains=location)
            
            # مرتب‌سازی
            order_by = search_params.get('order_by', '-rating')
            queryset = queryset.order_by(order_by)
            
            # صفحه‌بندی
            page = search_params.get('page', 1)
            page_size = search_params.get('page_size', 20)
            start = (page - 1) * page_size
            end = start + page_size
            
            doctors = queryset[start:end]
            total_count = queryset.count()
            
            return True, {
                'doctors': doctors,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'has_next': end < total_count
            }
            
        except Exception as e:
            self.logger.error(f"Error searching doctors: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}


class DoctorScheduleService:
    """
    سرویس مدیریت برنامه کاری پزشک
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.orchestrator = DoctorCentralOrchestrator()
    
    def create_schedule(self, user: User, schedule_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد برنامه کاری
        
        Args:
            user: کاربر پزشک
            schedule_data: داده‌های برنامه کاری
            
        Returns:
            (success, result_data or error_info)
        """
        try:
            # اجرای workflow ایجاد برنامه کاری
            result = self.orchestrator.execute_doctor_workflow(
                'create_schedule',
                schedule_data,
                user
            )
            
            if result.status.value == 'completed':
                schedule = result.data.get('create_schedule', {}).get('schedule')
                return True, {
                    'schedule_id': str(schedule.id),
                    'message': 'برنامه کاری با موفقیت ایجاد شد',
                    'warnings': result.warnings
                }
            else:
                return False, {
                    'error': 'خطا در ایجاد برنامه کاری',
                    'details': result.errors
                }
                
        except Exception as e:
            self.logger.error(f"Error creating schedule: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}
    
    def get_doctor_schedule(self, user: User, weekday: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت برنامه کاری پزشک
        
        Args:
            user: کاربر پزشک
            weekday: روز هفته (اختیاری)
            
        Returns:
            (success, schedule_data or error_info)
        """
        try:
            queryset = DoctorSchedule.objects.filter(doctor=user, is_active=True)
            
            if weekday is not None:
                queryset = queryset.filter(weekday=weekday)
            
            schedules = queryset.order_by('weekday', 'start_time')
            
            return True, {
                'schedules': schedules,
                'count': schedules.count()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting doctor schedule: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}
    
    def update_schedule(self, user: User, schedule_id: str, 
                       schedule_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        بروزرسانی برنامه کاری
        
        Args:
            user: کاربر پزشک
            schedule_id: شناسه برنامه کاری
            schedule_data: داده‌های جدید
            
        Returns:
            (success, result_data or error_info)
        """
        try:
            schedule = DoctorSchedule.objects.get(
                id=schedule_id,
                doctor=user,
                is_active=True
            )
            
            # فیلدهای قابل ویرایش
            editable_fields = [
                'start_time', 'end_time', 'visit_type', 'max_patients',
                'break_start', 'break_end'
            ]
            
            # بروزرسانی فیلدها
            for field in editable_fields:
                if field in schedule_data:
                    setattr(schedule, field, schedule_data[field])
            
            schedule.full_clean()  # اعتبارسنجی
            schedule.save()
            
            self.logger.info(f"Schedule {schedule_id} updated for doctor {user.id}")
            
            return True, {
                'schedule_id': str(schedule.id),
                'message': 'برنامه کاری با موفقیت بروزرسانی شد'
            }
            
        except DoctorSchedule.DoesNotExist:
            return False, {'error': 'برنامه کاری یافت نشد'}
        except ValidationError as e:
            return False, {'error': 'خطای اعتبارسنجی', 'details': str(e)}
        except Exception as e:
            self.logger.error(f"Error updating schedule: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}
    
    def delete_schedule(self, user: User, schedule_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        حذف برنامه کاری
        
        Args:
            user: کاربر پزشک
            schedule_id: شناسه برنامه کاری
            
        Returns:
            (success, result_data or error_info)
        """
        try:
            schedule = DoctorSchedule.objects.get(
                id=schedule_id,
                doctor=user,
                is_active=True
            )
            
            # حذف نرم
            schedule.is_active = False
            schedule.save()
            
            self.logger.info(f"Schedule {schedule_id} deleted for doctor {user.id}")
            
            return True, {'message': 'برنامه کاری با موفقیت حذف شد'}
            
        except DoctorSchedule.DoesNotExist:
            return False, {'error': 'برنامه کاری یافت نشد'}
        except Exception as e:
            self.logger.error(f"Error deleting schedule: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}


class DoctorCertificateService:
    """
    سرویس مدیریت مدارک پزشک
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def add_certificate(self, user: User, certificate_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        افزودن مدرک
        
        Args:
            user: کاربر پزشک
            certificate_data: داده‌های مدرک
            
        Returns:
            (success, result_data or error_info)
        """
        try:
            certificate = DoctorCertificate.objects.create(
                doctor=user,
                **certificate_data
            )
            
            self.logger.info(f"Certificate added for doctor {user.id}")
            
            return True, {
                'certificate_id': str(certificate.id),
                'message': 'مدرک با موفقیت افزوده شد'
            }
            
        except ValidationError as e:
            return False, {'error': 'خطای اعتبارسنجی', 'details': str(e)}
        except Exception as e:
            self.logger.error(f"Error adding certificate: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}
    
    def get_doctor_certificates(self, user: User, certificate_type: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت مدارک پزشک
        
        Args:
            user: کاربر پزشک
            certificate_type: نوع مدرک (اختیاری)
            
        Returns:
            (success, certificates_data or error_info)
        """
        try:
            queryset = DoctorCertificate.objects.filter(doctor=user, is_active=True)
            
            if certificate_type:
                queryset = queryset.filter(certificate_type=certificate_type)
            
            certificates = queryset.order_by('-issue_date')
            
            return True, {
                'certificates': certificates,
                'count': certificates.count()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting certificates: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}


class DoctorRatingService:
    """
    سرویس مدیریت امتیازدهی پزشک
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def add_rating(self, patient_user: User, doctor_user: User, 
                  rating_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        افزودن امتیاز به پزشک
        
        Args:
            patient_user: کاربر بیمار
            doctor_user: کاربر پزشک
            rating_data: داده‌های امتیاز
            
        Returns:
            (success, result_data or error_info)
        """
        try:
            # بررسی امتیاز قبلی
            visit_date = rating_data.get('visit_date')
            existing_rating = DoctorRating.objects.filter(
                doctor=doctor_user,
                patient=patient_user,
                visit_date=visit_date,
                is_active=True
            ).first()
            
            if existing_rating:
                return False, {'error': 'قبلاً برای این ویزیت امتیاز داده‌اید'}
            
            # ایجاد امتیاز جدید
            rating = DoctorRating.objects.create(
                doctor=doctor_user,
                patient=patient_user,
                **rating_data
            )
            
            self.logger.info(f"Rating added for doctor {doctor_user.id} by patient {patient_user.id}")
            
            return True, {
                'rating_id': str(rating.id),
                'message': 'امتیاز با موفقیت ثبت شد'
            }
            
        except ValidationError as e:
            return False, {'error': 'خطای اعتبارسنجی', 'details': str(e)}
        except Exception as e:
            self.logger.error(f"Error adding rating: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}
    
    def get_doctor_ratings(self, doctor_user: User, page: int = 1, 
                          page_size: int = 20) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت امتیازات پزشک
        
        Args:
            doctor_user: کاربر پزشک
            page: شماره صفحه
            page_size: اندازه صفحه
            
        Returns:
            (success, ratings_data or error_info)
        """
        try:
            queryset = DoctorRating.objects.filter(
                doctor=doctor_user,
                is_approved=True,
                is_active=True
            ).order_by('-created_at')
            
            # صفحه‌بندی
            start = (page - 1) * page_size
            end = start + page_size
            
            ratings = queryset[start:end]
            total_count = queryset.count()
            
            # آمار کلی
            stats = queryset.aggregate(
                avg_rating=Avg('rating'),
                total_ratings=Count('id')
            )
            
            return True, {
                'ratings': ratings,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'has_next': end < total_count,
                'stats': stats
            }
            
        except Exception as e:
            self.logger.error(f"Error getting ratings: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}


class DoctorAnalyticsService:
    """
    سرویس آنالیتیکس پزشک
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_doctor_dashboard_stats(self, user: User, 
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت آمار داشبورد پزشک
        
        Args:
            user: کاربر پزشک
            start_date: تاریخ شروع (اختیاری)
            end_date: تاریخ پایان (اختیاری)
            
        Returns:
            (success, stats_data or error_info)
        """
        try:
            if not start_date:
                start_date = timezone.now() - timedelta(days=30)
            if not end_date:
                end_date = timezone.now()
            
            # آمار امتیازات
            ratings_stats = DoctorRating.objects.filter(
                doctor=user,
                is_approved=True,
                is_active=True,
                created_at__range=[start_date, end_date]
            ).aggregate(
                avg_rating=Avg('rating'),
                total_ratings=Count('id')
            )
            
            # آمار برنامه کاری
            schedules_count = DoctorSchedule.objects.filter(
                doctor=user,
                is_active=True
            ).count()
            
            # آمار مدارک
            certificates_stats = DoctorCertificate.objects.filter(
                doctor=user,
                is_active=True
            ).aggregate(
                total_certificates=Count('id'),
                verified_certificates=Count('id', filter=Q(is_verified=True))
            )
            
            stats = {
                'period': {
                    'start_date': start_date.date(),
                    'end_date': end_date.date()
                },
                'ratings': {
                    'average': ratings_stats['avg_rating'] or 0.0,
                    'total': ratings_stats['total_ratings']
                },
                'schedules': {
                    'total_schedules': schedules_count
                },
                'certificates': certificates_stats,
                'profile': {
                    'is_verified': user.doctor_profile.is_verified if hasattr(user, 'doctor_profile') else False
                }
            }
            
            return True, {'stats': stats}
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard stats: {str(e)}")
            return False, {'error': 'خطای داخلی سرور'}