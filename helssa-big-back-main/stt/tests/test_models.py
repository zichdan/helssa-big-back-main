"""
تست‌های مربوط به مدل‌های STT
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import timedelta
import uuid

from ..models import STTTask, STTQualityControl, STTUsageStats

User = get_user_model()


class STTTaskModelTest(TestCase):
    """تست مدل STTTask"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            password='testpass123',
            user_type='patient'
        )
        
        # ایجاد فایل صوتی موک
        self.audio_content = b'fake audio content'
        self.audio_file = ContentFile(self.audio_content, 'test.mp3')
    
    def test_create_stt_task(self):
        """تست ایجاد وظیفه STT"""
        task = STTTask.objects.create(
            user=self.user,
            user_type='patient',
            audio_file=self.audio_file,
            file_size=len(self.audio_content),
            language='fa',
            model_used='base'
        )
        
        self.assertIsNotNone(task.task_id)
        self.assertEqual(task.status, 'pending')
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.user_type, 'patient')
        self.assertEqual(task.language, 'fa')
    
    def test_task_id_uniqueness(self):
        """تست یکتا بودن task_id"""
        task1 = STTTask.objects.create(
            user=self.user,
            user_type='patient',
            audio_file=self.audio_file,
            file_size=100
        )
        
        task2 = STTTask.objects.create(
            user=self.user,
            user_type='patient',
            audio_file=self.audio_file,
            file_size=200
        )
        
        self.assertNotEqual(task1.task_id, task2.task_id)
    
    def test_processing_time_calculation(self):
        """تست محاسبه زمان پردازش"""
        task = STTTask.objects.create(
            user=self.user,
            user_type='patient',
            audio_file=self.audio_file,
            file_size=100
        )
        
        # بدون زمان شروع و پایان
        self.assertIsNone(task.processing_time)
        
        # با زمان شروع و پایان
        task.started_at = timezone.now()
        task.completed_at = task.started_at + timedelta(seconds=30)
        task.save()
        
        self.assertAlmostEqual(task.processing_time, 30.0, places=1)
    
    def test_can_cancel(self):
        """تست امکان لغو وظیفه"""
        task = STTTask.objects.create(
            user=self.user,
            user_type='patient',
            audio_file=self.audio_file,
            file_size=100
        )
        
        # وضعیت‌های قابل لغو
        task.status = 'pending'
        self.assertTrue(task.can_cancel())
        
        task.status = 'processing'
        self.assertTrue(task.can_cancel())
        
        # وضعیت‌های غیرقابل لغو
        task.status = 'completed'
        self.assertFalse(task.can_cancel())
        
        task.status = 'failed'
        self.assertFalse(task.can_cancel())
        
        task.status = 'cancelled'
        self.assertFalse(task.can_cancel())
    
    def test_file_size_validation(self):
        """تست اعتبارسنجی حجم فایل"""
        from django.core.exceptions import ValidationError
        
        task = STTTask(
            user=self.user,
            user_type='patient',
            audio_file=self.audio_file,
            file_size=52428801  # بیش از 50MB
        )
        
        with self.assertRaises(ValidationError):
            task.full_clean()


class STTQualityControlModelTest(TestCase):
    """تست مدل STTQualityControl"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            password='testpass123',
            user_type='doctor'
        )
        
        self.reviewer = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        
        self.audio_file = ContentFile(b'fake audio', 'test.mp3')
        
        self.task = STTTask.objects.create(
            user=self.user,
            user_type='doctor',
            audio_file=self.audio_file,
            file_size=100,
            transcription='تست متن تبدیل شده',
            confidence_score=0.85
        )
    
    def test_create_quality_control(self):
        """تست ایجاد کنترل کیفیت"""
        qc = STTQualityControl.objects.create(
            task=self.task,
            audio_quality_score=0.75,
            background_noise_level='low',
            speech_clarity='clear',
            needs_human_review=False
        )
        
        self.assertEqual(qc.task, self.task)
        self.assertEqual(qc.audio_quality_score, 0.75)
        self.assertEqual(qc.background_noise_level, 'low')
        self.assertEqual(qc.speech_clarity, 'clear')
        self.assertFalse(qc.needs_human_review)
    
    def test_one_to_one_relation(self):
        """تست رابطه one-to-one با task"""
        qc1 = STTQualityControl.objects.create(
            task=self.task,
            audio_quality_score=0.5,
            background_noise_level='medium',
            speech_clarity='moderate'
        )
        
        # تلاش برای ایجاد کنترل کیفیت دوم برای همان task
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            STTQualityControl.objects.create(
                task=self.task,
                audio_quality_score=0.6,
                background_noise_level='low',
                speech_clarity='clear'
            )
    
    def test_medical_terms_json_field(self):
        """تست فیلد JSON برای اصطلاحات پزشکی"""
        medical_terms = [
            {'term': 'دیابت', 'position': 10},
            {'term': 'متفورمین', 'position': 25}
        ]
        
        qc = STTQualityControl.objects.create(
            task=self.task,
            audio_quality_score=0.8,
            background_noise_level='low',
            speech_clarity='clear',
            medical_terms_detected=medical_terms
        )
        
        qc.refresh_from_db()
        self.assertEqual(len(qc.medical_terms_detected), 2)
        self.assertEqual(qc.medical_terms_detected[0]['term'], 'دیابت')
    
    def test_review_workflow(self):
        """تست فرآیند بررسی"""
        qc = STTQualityControl.objects.create(
            task=self.task,
            audio_quality_score=0.3,
            background_noise_level='high',
            speech_clarity='unclear',
            needs_human_review=True,
            review_reason='کیفیت پایین صدا'
        )
        
        self.assertTrue(qc.needs_human_review)
        self.assertIsNone(qc.reviewed_by)
        self.assertIsNone(qc.reviewed_at)
        
        # انجام بررسی
        qc.corrected_transcription = 'متن اصلاح شده'
        qc.reviewed_by = self.reviewer
        qc.reviewed_at = timezone.now()
        qc.needs_human_review = False
        qc.save()
        
        self.assertFalse(qc.needs_human_review)
        self.assertEqual(qc.reviewed_by, self.reviewer)
        self.assertIsNotNone(qc.reviewed_at)


class STTUsageStatsModelTest(TestCase):
    """تست مدل STTUsageStats"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            password='testpass123',
            user_type='patient'
        )
        
        self.today = timezone.now().date()
    
    def test_create_usage_stats(self):
        """تست ایجاد آمار استفاده"""
        stats = STTUsageStats.objects.create(
            user=self.user,
            date=self.today,
            total_requests=10,
            successful_requests=8,
            failed_requests=2,
            total_audio_duration=300.5,
            total_processing_time=150.2,
            average_confidence_score=0.82
        )
        
        self.assertEqual(stats.user, self.user)
        self.assertEqual(stats.date, self.today)
        self.assertEqual(stats.total_requests, 10)
        self.assertEqual(stats.successful_requests, 8)
        self.assertEqual(stats.failed_requests, 2)
    
    def test_unique_constraint(self):
        """تست محدودیت یکتایی user-date"""
        STTUsageStats.objects.create(
            user=self.user,
            date=self.today,
            total_requests=5
        )
        
        # تلاش برای ایجاد آمار دوم برای همان کاربر و تاریخ
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            STTUsageStats.objects.create(
                user=self.user,
                date=self.today,
                total_requests=10
            )
    
    def test_stats_calculation(self):
        """تست محاسبات آماری"""
        stats = STTUsageStats.objects.create(
            user=self.user,
            date=self.today,
            total_requests=100,
            successful_requests=85,
            failed_requests=15
        )
        
        # محاسبه نرخ موفقیت
        success_rate = (stats.successful_requests / stats.total_requests) * 100
        self.assertEqual(success_rate, 85.0)
        
        # بررسی جمع درخواست‌ها
        total = stats.successful_requests + stats.failed_requests
        self.assertEqual(total, stats.total_requests)