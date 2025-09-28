"""
سرویس مدیریت امتیازدهی جلسات
"""

import logging
from typing import Dict, Any, Optional, List
from django.db.models import Avg, Count, Q
from django.contrib.auth import get_user_model

from ..models import SessionRating

User = get_user_model()
logger = logging.getLogger(__name__)


class RatingService:
    """
    سرویس امتیازدهی جلسات
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_rating(self, user, session_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ایجاد امتیازدهی جدید
        
        Args:
            user: کاربر امتیازدهنده
            session_id: شناسه جلسه
            data: داده‌های امتیازدهی
            
        Returns:
            dict: نتیجه ایجاد امتیازدهی
        """
        try:
            # بررسی وجود امتیازدهی قبلی
            existing_rating = SessionRating.objects.filter(
                session_id=session_id,
                user=user,
                is_active=True
            ).first()
            
            if existing_rating:
                return {
                    'success': False,
                    'error': 'already_rated',
                    'message': 'شما قبلاً به این جلسه امتیاز داده‌اید'
                }
            
            # ایجاد امتیازدهی
            rating = SessionRating.objects.create(
                session_id=session_id,
                user=user,
                overall_rating=data['overall_rating'],
                response_quality=data.get('response_quality'),
                response_speed=data.get('response_speed'),
                helpfulness=data.get('helpfulness'),
                comment=data.get('comment', ''),
                suggestions=data.get('suggestions', ''),
                would_recommend=data.get('would_recommend')
            )
            
            self.logger.info(f"Rating created for session {session_id} by user {user.id}")
            
            return {
                'success': True,
                'rating_id': str(rating.id),
                'message': 'امتیازدهی با موفقیت ثبت شد'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating rating: {str(e)}")
            return {
                'success': False,
                'error': 'creation_failed',
                'message': 'خطا در ثبت امتیازدهی'
            }
    
    def get_user_ratings(self, user, limit: Optional[int] = None) -> List[SessionRating]:
        """
        دریافت امتیازدهی‌های کاربر
        
        Args:
            user: کاربر
            limit: محدودیت تعداد
            
        Returns:
            list: فهرست امتیازدهی‌ها
        """
        queryset = SessionRating.objects.filter(
            user=user,
            is_active=True
        ).order_by('-created_at')
        
        if limit:
            queryset = queryset[:limit]
            
        return list(queryset)
    
    def get_session_rating(self, session_id: str) -> Optional[SessionRating]:
        """
        دریافت امتیازدهی جلسه
        
        Args:
            session_id: شناسه جلسه
            
        Returns:
            SessionRating یا None
        """
        return SessionRating.objects.filter(
            session_id=session_id,
            is_active=True
        ).first()
    
    def get_rating_stats(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        محاسبه آمار امتیازدهی‌ها
        
        Args:
            filters: فیلترهای اختیاری
            
        Returns:
            dict: آمار امتیازدهی‌ها
        """
        try:
            queryset = SessionRating.objects.filter(is_active=True)
            
            # اعمال فیلترها
            if filters:
                if filters.get('start_date'):
                    queryset = queryset.filter(created_at__gte=filters['start_date'])
                if filters.get('end_date'):
                    queryset = queryset.filter(created_at__lte=filters['end_date'])
                if filters.get('min_rating'):
                    queryset = queryset.filter(overall_rating__gte=filters['min_rating'])
            
            total_ratings = queryset.count()
            
            if total_ratings == 0:
                return {
                    'total_ratings': 0,
                    'average_overall': 0,
                    'recommendation_rate': 0,
                    'rating_distribution': {},
                    'message': 'هنوز امتیازدهی وجود ندارد'
                }
            
            # محاسبه میانگین‌ها
            averages = queryset.aggregate(
                average_overall=Avg('overall_rating'),
                average_quality=Avg('response_quality'),
                average_speed=Avg('response_speed'),
                average_helpfulness=Avg('helpfulness')
            )
            
            # توزیع امتیازات
            rating_distribution = {}
            for i in range(1, 6):
                count = queryset.filter(overall_rating=i).count()
                percentage = (count / total_ratings) * 100
                rating_distribution[str(i)] = {
                    'count': count,
                    'percentage': round(percentage, 1)
                }
            
            # نرخ توصیه
            recommendation_count = queryset.filter(would_recommend=True).count()
            recommendation_rate = (recommendation_count / total_ratings) * 100
            
            # آخرین نظرات
            recent_comments = list(
                queryset.filter(comment__isnull=False, comment__gt='')
                .values_list('comment', flat=True)[:5]
            )
            
            return {
                'total_ratings': total_ratings,
                'average_overall': round(averages['average_overall'] or 0, 2),
                'average_quality': round(averages['average_quality'] or 0, 2),
                'average_speed': round(averages['average_speed'] or 0, 2),
                'average_helpfulness': round(averages['average_helpfulness'] or 0, 2),
                'recommendation_rate': round(recommendation_rate, 2),
                'rating_distribution': rating_distribution,
                'recent_comments': recent_comments,
                'satisfaction_level': self._calculate_satisfaction_level(averages['average_overall'] or 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating rating stats: {str(e)}")
            return {
                'error': 'calculation_failed',
                'message': 'خطا در محاسبه آمار'
            }
    
    def update_rating(self, rating_id: str, user, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ویرایش امتیازدهی
        
        Args:
            rating_id: شناسه امتیازدهی
            user: کاربر
            data: داده‌های جدید
            
        Returns:
            dict: نتیجه ویرایش
        """
        try:
            rating = SessionRating.objects.get(
                id=rating_id,
                user=user,
                is_active=True
            )
            
            # ویرایش فیلدها
            if 'overall_rating' in data:
                rating.overall_rating = data['overall_rating']
            if 'response_quality' in data:
                rating.response_quality = data['response_quality']
            if 'response_speed' in data:
                rating.response_speed = data['response_speed']
            if 'helpfulness' in data:
                rating.helpfulness = data['helpfulness']
            if 'comment' in data:
                rating.comment = data['comment']
            if 'suggestions' in data:
                rating.suggestions = data['suggestions']
            if 'would_recommend' in data:
                rating.would_recommend = data['would_recommend']
            
            rating.save()
            
            self.logger.info(f"Rating {rating_id} updated by user {user.id}")
            
            return {
                'success': True,
                'message': 'امتیازدهی با موفقیت ویرایش شد'
            }
            
        except SessionRating.DoesNotExist:
            return {
                'success': False,
                'error': 'not_found',
                'message': 'امتیازدهی یافت نشد'
            }
        except Exception as e:
            self.logger.error(f"Error updating rating: {str(e)}")
            return {
                'success': False,
                'error': 'update_failed',
                'message': 'خطا در ویرایش امتیازدهی'
            }
    
    def delete_rating(self, rating_id: str, user) -> Dict[str, Any]:
        """
        حذف امتیازدهی (soft delete)
        
        Args:
            rating_id: شناسه امتیازدهی
            user: کاربر
            
        Returns:
            dict: نتیجه حذف
        """
        try:
            rating = SessionRating.objects.get(
                id=rating_id,
                user=user,
                is_active=True
            )
            
            rating.soft_delete()
            
            self.logger.info(f"Rating {rating_id} deleted by user {user.id}")
            
            return {
                'success': True,
                'message': 'امتیازدهی حذف شد'
            }
            
        except SessionRating.DoesNotExist:
            return {
                'success': False,
                'error': 'not_found',
                'message': 'امتیازدهی یافت نشد'
            }
        except Exception as e:
            self.logger.error(f"Error deleting rating: {str(e)}")
            return {
                'success': False,
                'error': 'deletion_failed',
                'message': 'خطا در حذف امتیازدهی'
            }
    
    def _calculate_satisfaction_level(self, average_rating: float) -> str:
        """
        محاسبه سطح رضایت بر اساس میانگین امتیاز
        
        Args:
            average_rating: میانگین امتیاز
            
        Returns:
            str: سطح رضایت
        """
        if average_rating >= 4.5:
            return 'excellent'  # عالی
        elif average_rating >= 4.0:
            return 'very_good'  # خیلی خوب
        elif average_rating >= 3.5:
            return 'good'  # خوب
        elif average_rating >= 3.0:
            return 'average'  # متوسط
        elif average_rating >= 2.0:
            return 'poor'  # ضعیف
        else:
            return 'very_poor'  # خیلی ضعیف
    
    def get_low_ratings(self, threshold: int = 2) -> List[SessionRating]:
        """
        دریافت امتیازدهی‌های پایین
        
        Args:
            threshold: آستانه امتیاز پایین
            
        Returns:
            list: فهرست امتیازدهی‌های پایین
        """
        return list(
            SessionRating.objects.filter(
                overall_rating__lte=threshold,
                is_active=True
            ).order_by('-created_at')
        )
    
    def get_trending_ratings(self, days: int = 7) -> Dict[str, Any]:
        """
        دریافت روند امتیازدهی‌ها
        
        Args:
            days: تعداد روزهای اخیر
            
        Returns:
            dict: روند امتیازدهی‌ها
        """
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        current_period = SessionRating.objects.filter(
            created_at__gte=start_date,
            is_active=True
        )
        
        previous_start = start_date - timedelta(days=days)
        previous_period = SessionRating.objects.filter(
            created_at__gte=previous_start,
            created_at__lt=start_date,
            is_active=True
        )
        
        current_avg = current_period.aggregate(avg=Avg('overall_rating'))['avg'] or 0
        previous_avg = previous_period.aggregate(avg=Avg('overall_rating'))['avg'] or 0
        
        trend = 'stable'
        if current_avg > previous_avg + 0.1:
            trend = 'increasing'
        elif current_avg < previous_avg - 0.1:
            trend = 'decreasing'
        
        return {
            'current_average': round(current_avg, 2),
            'previous_average': round(previous_avg, 2),
            'trend': trend,
            'change': round(current_avg - previous_avg, 2),
            'current_count': current_period.count(),
            'previous_count': previous_period.count()
        }