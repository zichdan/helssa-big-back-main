"""
Orchestrator Core برای feedback app
هماهنگی بین هسته‌ها و مدیریت workflow
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import core if available
try:
    from app_standards.four_cores.orchestrator import (
        CentralOrchestrator, WorkflowStatus, WorkflowStep, WorkflowResult
    )
except ImportError:
    # Fallback if app_standards doesn't exist
    class WorkflowStatus(Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"
    
    @dataclass
    class WorkflowStep:
        name: str
        status: WorkflowStatus
        result: Optional[Dict[str, Any]] = None
        error: Optional[str] = None
        start_time: Optional[float] = None
        end_time: Optional[float] = None
    
    @dataclass
    class WorkflowResult:
        success: bool
        steps: List[WorkflowStep]
        final_result: Optional[Dict[str, Any]] = None
        error: Optional[str] = None
        metadata: Dict[str, Any] = None
    
    class CentralOrchestrator:
        def __init__(self):
            self.logger = logging.getLogger(__name__)


class FeedbackOrchestrator(CentralOrchestrator):
    """
    هسته اصلی هماهنگی برای مدیریت فرآیندهای feedback
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # import cores
        from .api_ingress import FeedbackAPIIngressCore
        from .text_processor import FeedbackTextProcessorCore
        from .speech_processor import FeedbackSpeechProcessorCore
        
        self.api_ingress = FeedbackAPIIngressCore()
        self.text_processor = FeedbackTextProcessorCore()
        self.speech_processor = FeedbackSpeechProcessorCore()
    
    async def process_session_rating(self, data: Dict[str, Any], user) -> WorkflowResult:
        """
        پردازش کامل امتیازدهی جلسه
        
        Args:
            data: داده‌های امتیازدهی
            user: کاربر امتیازدهنده
            
        Returns:
            WorkflowResult: نتیجه کامل فرآیند
        """
        steps = []
        
        try:
            # مرحله 1: اعتبارسنجی داده‌ها
            step1 = WorkflowStep("validate_data", WorkflowStatus.IN_PROGRESS)
            steps.append(step1)
            
            is_valid, validation_result = self.api_ingress.validate_rating_data(data)
            if not is_valid:
                step1.status = WorkflowStatus.FAILED
                step1.error = validation_result.get('error')
                return WorkflowResult(False, steps, error=validation_result.get('error'))
            
            step1.status = WorkflowStatus.COMPLETED
            step1.result = validation_result
            
            # مرحله 2: پردازش متن نظرات
            if validation_result.get('comment'):
                step2 = WorkflowStep("process_comment_text", WorkflowStatus.IN_PROGRESS)
                steps.append(step2)
                
                text_result = self.text_processor.process_feedback_text(
                    validation_result['comment'], 
                    'session_rating'
                )
                
                step2.status = WorkflowStatus.COMPLETED
                step2.result = {
                    'sentiment': text_result.sentiment,
                    'keywords': text_result.keywords,
                    'metadata': text_result.metadata
                }
            
            # مرحله 3: ذخیره در دیتابیس
            step3 = WorkflowStep("save_rating", WorkflowStatus.IN_PROGRESS)
            steps.append(step3)
            
            rating_data = await self._save_session_rating(validation_result, user)
            
            step3.status = WorkflowStatus.COMPLETED
            step3.result = rating_data
            
            # مرحله 4: ارسال اعلان (اختیاری)
            step4 = WorkflowStep("send_notification", WorkflowStatus.IN_PROGRESS)
            steps.append(step4)
            
            notification_result = await self._send_rating_notification(rating_data, user)
            
            step4.status = WorkflowStatus.COMPLETED
            step4.result = notification_result
            
            return WorkflowResult(
                success=True,
                steps=steps,
                final_result={
                    'rating_id': rating_data['id'],
                    'message': 'امتیازدهی با موفقیت ثبت شد'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in session rating workflow: {str(e)}")
            
            # علامت‌گذاری مرحله جاری به عنوان ناموفق
            if steps and steps[-1].status == WorkflowStatus.IN_PROGRESS:
                steps[-1].status = WorkflowStatus.FAILED
                steps[-1].error = str(e)
            
            return WorkflowResult(False, steps, error=str(e))
    
    async def process_message_feedback(self, data: Dict[str, Any], user) -> WorkflowResult:
        """
        پردازش کامل بازخورد پیام
        
        Args:
            data: داده‌های بازخورد
            user: کاربر بازخورددهنده
            
        Returns:
            WorkflowResult: نتیجه کامل فرآیند
        """
        steps = []
        
        try:
            # مرحله 1: اعتبارسنجی
            step1 = WorkflowStep("validate_feedback_data", WorkflowStatus.IN_PROGRESS)
            steps.append(step1)
            
            is_valid, validation_result = self.api_ingress.validate_feedback_data(data)
            if not is_valid:
                step1.status = WorkflowStatus.FAILED
                step1.error = validation_result.get('error')
                return WorkflowResult(False, steps, error=validation_result.get('error'))
            
            step1.status = WorkflowStatus.COMPLETED
            step1.result = validation_result
            
            # مرحله 2: پردازش متن تفصیلی
            if validation_result.get('detailed_feedback'):
                step2 = WorkflowStep("analyze_detailed_feedback", WorkflowStatus.IN_PROGRESS)
                steps.append(step2)
                
                text_analysis = self.text_processor.process_feedback_text(
                    validation_result['detailed_feedback'],
                    'message_feedback'
                )
                
                step2.status = WorkflowStatus.COMPLETED
                step2.result = {
                    'analysis': text_analysis.metadata,
                    'requires_attention': text_analysis.metadata.get('medical_concerns', {}).get('requires_followup', False)
                }
            
            # مرحله 3: ذخیره بازخورد
            step3 = WorkflowStep("save_feedback", WorkflowStatus.IN_PROGRESS)
            steps.append(step3)
            
            feedback_data = await self._save_message_feedback(validation_result, user)
            
            step3.status = WorkflowStatus.COMPLETED
            step3.result = feedback_data
            
            # مرحله 4: بررسی نیاز به پیگیری
            if any(step.result and step.result.get('requires_attention') for step in steps):
                step4 = WorkflowStep("create_followup_task", WorkflowStatus.IN_PROGRESS)
                steps.append(step4)
                
                followup_result = await self._create_followup_task(feedback_data, user)
                
                step4.status = WorkflowStatus.COMPLETED
                step4.result = followup_result
            
            return WorkflowResult(
                success=True,
                steps=steps,
                final_result={
                    'feedback_id': feedback_data['id'],
                    'message': 'بازخورد شما ثبت شد'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in message feedback workflow: {str(e)}")
            
            if steps and steps[-1].status == WorkflowStatus.IN_PROGRESS:
                steps[-1].status = WorkflowStatus.FAILED
                steps[-1].error = str(e)
            
            return WorkflowResult(False, steps, error=str(e))
    
    async def process_voice_feedback(self, audio_data: bytes, format: str, user) -> WorkflowResult:
        """
        پردازش کامل بازخورد صوتی
        
        Args:
            audio_data: داده‌های صوتی
            format: فرمت فایل
            user: کاربر
            
        Returns:
            WorkflowResult: نتیجه فرآیند
        """
        steps = []
        
        try:
            # مرحله 1: اعتبارسنجی صوت
            step1 = WorkflowStep("validate_audio", WorkflowStatus.IN_PROGRESS)
            steps.append(step1)
            
            is_valid, error_msg = self.speech_processor.validate_audio_feedback(audio_data, format)
            if not is_valid:
                step1.status = WorkflowStatus.FAILED
                step1.error = error_msg
                return WorkflowResult(False, steps, error=error_msg)
            
            step1.status = WorkflowStatus.COMPLETED
            
            # مرحله 2: تبدیل صدا به متن
            step2 = WorkflowStep("transcribe_audio", WorkflowStatus.IN_PROGRESS)
            steps.append(step2)
            
            transcription = self.speech_processor.transcribe_feedback_audio(audio_data, format)
            
            step2.status = WorkflowStatus.COMPLETED
            step2.result = {
                'text': transcription.text,
                'confidence': transcription.confidence
            }
            
            # مرحله 3: پردازش متن حاصل
            step3 = WorkflowStep("analyze_transcribed_text", WorkflowStatus.IN_PROGRESS)
            steps.append(step3)
            
            if transcription.text:
                text_analysis = self.text_processor.process_feedback_text(
                    transcription.text,
                    'voice_feedback'
                )
                
                step3.status = WorkflowStatus.COMPLETED
                step3.result = {
                    'sentiment': text_analysis.sentiment,
                    'keywords': text_analysis.keywords,
                    'analysis': text_analysis.metadata
                }
            else:
                step3.status = WorkflowStatus.FAILED
                step3.error = "نتوانستیم صدای شما را تشخیص دهیم"
                return WorkflowResult(False, steps, error="تشخیص صدا ناموفق بود")
            
            # مرحله 4: ذخیره در دیتابیس
            step4 = WorkflowStep("save_voice_feedback", WorkflowStatus.IN_PROGRESS)
            steps.append(step4)
            
            voice_feedback_data = await self._save_voice_feedback(
                transcription, text_analysis, audio_data, format, user
            )
            
            step4.status = WorkflowStatus.COMPLETED
            step4.result = voice_feedback_data
            
            return WorkflowResult(
                success=True,
                steps=steps,
                final_result={
                    'feedback_id': voice_feedback_data['id'],
                    'transcribed_text': transcription.text,
                    'message': 'بازخورد صوتی شما ثبت شد'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in voice feedback workflow: {str(e)}")
            
            if steps and steps[-1].status == WorkflowStatus.IN_PROGRESS:
                steps[-1].status = WorkflowStatus.FAILED
                steps[-1].error = str(e)
            
            return WorkflowResult(False, steps, error=str(e))
    
    async def process_survey_submission(self, survey_id: str, answers: Dict[str, Any], user) -> WorkflowResult:
        """
        پردازش کامل ارسال نظرسنجی
        
        Args:
            survey_id: شناسه نظرسنجی
            answers: پاسخ‌های کاربر
            user: کاربر پاسخ‌دهنده
            
        Returns:
            WorkflowResult: نتیجه فرآیند
        """
        steps = []
        
        try:
            # مرحله 1: بررسی نظرسنجی
            step1 = WorkflowStep("validate_survey", WorkflowStatus.IN_PROGRESS)
            steps.append(step1)
            
            survey_validation = await self._validate_survey_submission(survey_id, user)
            if not survey_validation['valid']:
                step1.status = WorkflowStatus.FAILED
                step1.error = survey_validation['error']
                return WorkflowResult(False, steps, error=survey_validation['error'])
            
            step1.status = WorkflowStatus.COMPLETED
            step1.result = survey_validation
            
            # مرحله 2: پردازش پاسخ‌های متنی
            step2 = WorkflowStep("process_text_answers", WorkflowStatus.IN_PROGRESS)
            steps.append(step2)
            
            text_responses = []
            for key, value in answers.items():
                if isinstance(value, str) and value.strip():
                    analysis = self.text_processor.process_feedback_text(value, 'survey_response')
                    text_responses.append({
                        'question': key,
                        'answer': value,
                        'analysis': analysis.metadata
                    })
            
            step2.status = WorkflowStatus.COMPLETED
            step2.result = {'analyzed_responses': text_responses}
            
            # مرحله 3: محاسبه امتیاز کلی
            step3 = WorkflowStep("calculate_score", WorkflowStatus.IN_PROGRESS)
            steps.append(step3)
            
            overall_score = self._calculate_survey_score(answers, survey_validation['survey'])
            
            step3.status = WorkflowStatus.COMPLETED
            step3.result = {'overall_score': overall_score}
            
            # مرحله 4: ذخیره پاسخ
            step4 = WorkflowStep("save_survey_response", WorkflowStatus.IN_PROGRESS)
            steps.append(step4)
            
            response_data = await self._save_survey_response(
                survey_id, answers, overall_score, user
            )
            
            step4.status = WorkflowStatus.COMPLETED
            step4.result = response_data
            
            return WorkflowResult(
                success=True,
                steps=steps,
                final_result={
                    'response_id': response_data['id'],
                    'overall_score': overall_score,
                    'message': 'پاسخ‌های شما ثبت شد'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in survey submission workflow: {str(e)}")
            
            if steps and steps[-1].status == WorkflowStatus.IN_PROGRESS:
                steps[-1].status = WorkflowStatus.FAILED
                steps[-1].error = str(e)
            
            return WorkflowResult(False, steps, error=str(e))
    
    async def generate_feedback_analytics(self, filters: Dict[str, Any]) -> WorkflowResult:
        """
        تولید آنالیتیک جامع از بازخوردها
        
        Args:
            filters: فیلترهای مورد نظر
            
        Returns:
            WorkflowResult: نتیجه آنالیتیک
        """
        steps = []
        
        try:
            # مرحله 1: جمع‌آوری داده‌ها
            step1 = WorkflowStep("collect_feedback_data", WorkflowStatus.IN_PROGRESS)
            steps.append(step1)
            
            feedback_data = await self._collect_feedback_data(filters)
            
            step1.status = WorkflowStatus.COMPLETED
            step1.result = feedback_data
            
            # مرحله 2: تحلیل متن‌ها
            step2 = WorkflowStep("analyze_text_batch", WorkflowStatus.IN_PROGRESS)
            steps.append(step2)
            
            all_texts = feedback_data.get('text_feedbacks', [])
            batch_analysis = self.text_processor.summarize_feedback_batch(all_texts)
            
            step2.status = WorkflowStatus.COMPLETED
            step2.result = batch_analysis
            
            # مرحله 3: تولید آمار
            step3 = WorkflowStep("generate_statistics", WorkflowStatus.IN_PROGRESS)
            steps.append(step3)
            
            statistics = await self._generate_feedback_statistics(feedback_data, batch_analysis)
            
            step3.status = WorkflowStatus.COMPLETED
            step3.result = statistics
            
            return WorkflowResult(
                success=True,
                steps=steps,
                final_result={
                    'analytics': statistics,
                    'text_analysis': batch_analysis,
                    'data_summary': feedback_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generating feedback analytics: {str(e)}")
            
            if steps and steps[-1].status == WorkflowStatus.IN_PROGRESS:
                steps[-1].status = WorkflowStatus.FAILED
                steps[-1].error = str(e)
            
            return WorkflowResult(False, steps, error=str(e))
    
    # متدهای کمکی خصوصی
    
    async def _save_session_rating(self, data: Dict[str, Any], user) -> Dict[str, Any]:
        """ذخیره امتیازدهی جلسه"""
        # در پیاده‌سازی واقعی، از مدل SessionRating استفاده می‌شود
        return {
            'id': 'mock_rating_id',
            'session_id': data['session_id'],
            'user_id': str(user.id) if hasattr(user, 'id') else 'anonymous',
            'overall_rating': data['overall_rating']
        }
    
    async def _save_message_feedback(self, data: Dict[str, Any], user) -> Dict[str, Any]:
        """ذخیره بازخورد پیام"""
        return {
            'id': 'mock_feedback_id',
            'message_id': data['message_id'],
            'user_id': str(user.id) if hasattr(user, 'id') else 'anonymous',
            'feedback_type': data['feedback_type']
        }
    
    async def _save_voice_feedback(self, transcription, text_analysis, audio_data, format, user) -> Dict[str, Any]:
        """ذخیره بازخورد صوتی"""
        return {
            'id': 'mock_voice_feedback_id',
            'user_id': str(user.id) if hasattr(user, 'id') else 'anonymous',
            'transcribed_text': transcription.text,
            'confidence': transcription.confidence
        }
    
    async def _save_survey_response(self, survey_id: str, answers: Dict, score: float, user) -> Dict[str, Any]:
        """ذخیره پاسخ نظرسنجی"""
        return {
            'id': 'mock_response_id',
            'survey_id': survey_id,
            'user_id': str(user.id) if hasattr(user, 'id') else 'anonymous',
            'overall_score': score
        }
    
    async def _send_rating_notification(self, rating_data: Dict, user) -> Dict[str, Any]:
        """ارسال اعلان امتیازدهی"""
        return {'notification_sent': True}
    
    async def _create_followup_task(self, feedback_data: Dict, user) -> Dict[str, Any]:
        """ایجاد تسک پیگیری"""
        return {'followup_created': True}
    
    async def _validate_survey_submission(self, survey_id: str, user) -> Dict[str, Any]:
        """اعتبارسنجی ارسال نظرسنجی"""
        return {
            'valid': True,
            'survey': {'id': survey_id, 'title': 'نظرسنجی تست'}
        }
    
    def _calculate_survey_score(self, answers: Dict, survey: Dict) -> float:
        """محاسبه امتیاز نظرسنجی"""
        # محاسبه ساده بر اساس پاسخ‌های عددی
        numeric_answers = [v for v in answers.values() if isinstance(v, (int, float))]
        if numeric_answers:
            return sum(numeric_answers) / len(numeric_answers)
        return 0.0
    
    async def _collect_feedback_data(self, filters: Dict) -> Dict[str, Any]:
        """جمع‌آوری داده‌های بازخورد"""
        return {
            'text_feedbacks': ['بازخورد تست 1', 'بازخورد تست 2'],
            'ratings_count': 100,
            'surveys_count': 50
        }
    
    async def _generate_feedback_statistics(self, data: Dict, analysis: Dict) -> Dict[str, Any]:
        """تولید آمار بازخورد"""
        return {
            'total_feedbacks': data.get('ratings_count', 0) + data.get('surveys_count', 0),
            'sentiment_breakdown': analysis.get('sentiment_summary', {}),
            'average_rating': 4.2,
            'response_rate': 85.5
        }