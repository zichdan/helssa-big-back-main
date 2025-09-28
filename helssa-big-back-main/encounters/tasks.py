from celery import shared_task, chain, group
from typing import List, Dict, Optional
from django.utils import timezone
import asyncio
import logging

from .models import AudioChunk, Transcript, Encounter, SOAPReport
from .services import AudioProcessingService, SOAPGenerationService

logger = logging.getLogger(__name__)


@shared_task(queue='stt')
def process_audio_chunk_stt(chunk_id: str) -> Dict:
    """پردازش STT یک قطعه صوتی
    
    Args:
        chunk_id: شناسه قطعه صوتی
        
    Returns:
        اطلاعات پردازش
    """
    try:
        chunk = AudioChunk.objects.get(id=chunk_id)
        
        # به‌روزرسانی وضعیت
        chunk.transcription_status = 'processing'
        chunk.save()
        
        # TODO: اتصال به سرویس STT (Whisper)
        # فعلاً داده ساختگی
        transcript_text = f"رونویسی قطعه {chunk.chunk_index} از ملاقات"
        confidence = 0.85
        
        # ایجاد رونویسی
        transcript = Transcript.objects.create(
            audio_chunk=chunk,
            text=transcript_text,
            language='fa',
            confidence_score=confidence,
            word_timestamps=[],  # TODO: دریافت از Whisper
            stt_model='whisper-1',
            processing_time=5.2  # ثانیه
        )
        
        # به‌روزرسانی وضعیت
        chunk.transcription_status = 'completed'
        chunk.is_processed = True
        chunk.processed_at = timezone.now()
        chunk.save()
        
        # شروع استخراج موجودیت‌های پزشکی
        extract_medical_entities.delay(str(transcript.id))
        
        logger.info(f"STT completed for chunk {chunk_id}")
        
        return {
            'chunk_id': str(chunk.id),
            'transcript_id': str(transcript.id),
            'text_length': len(transcript_text),
            'confidence': confidence
        }
        
    except AudioChunk.DoesNotExist:
        logger.error(f"AudioChunk {chunk_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error processing STT for chunk {chunk_id}: {str(e)}")
        
        # به‌روزرسانی وضعیت خطا
        try:
            chunk = AudioChunk.objects.get(id=chunk_id)
            chunk.transcription_status = 'failed'
            chunk.save()
        except:
            pass
            
        raise


@shared_task(queue='nlp')
def extract_medical_entities(transcript_id: str) -> Dict:
    """استخراج موجودیت‌های پزشکی از رونویسی
    
    Args:
        transcript_id: شناسه رونویسی
        
    Returns:
        موجودیت‌های استخراج شده
    """
    try:
        transcript = Transcript.objects.get(id=transcript_id)
        
        # TODO: اتصال به سرویس NLP پزشکی
        # فعلاً داده ساختگی
        entities = {
            'entities': [
                {
                    'type': 'symptom',
                    'text': 'سردرد',
                    'start': 10,
                    'end': 15,
                    'confidence': 0.9
                },
                {
                    'type': 'medication',
                    'text': 'استامینوفن',
                    'start': 45,
                    'end': 55,
                    'confidence': 0.85
                }
            ],
            'extracted_at': timezone.now().isoformat()
        }
        
        # به‌روزرسانی transcript
        transcript.medical_entities = entities
        transcript.save()
        
        logger.info(f"Medical entities extracted for transcript {transcript_id}")
        
        return entities
        
    except Transcript.DoesNotExist:
        logger.error(f"Transcript {transcript_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error extracting entities for transcript {transcript_id}: {str(e)}")
        raise


@shared_task
def merge_encounter_transcripts(encounter_id: str) -> str:
    """ادغام رونویسی‌های یک ملاقات
    
    Args:
        encounter_id: شناسه ملاقات
        
    Returns:
        متن کامل رونویسی
    """
    try:
        # بازیابی تمام رونویسی‌ها
        transcripts = Transcript.objects.filter(
            audio_chunk__encounter_id=encounter_id
        ).order_by('audio_chunk__chunk_index').values_list('text', flat=True)
        
        if not transcripts:
            logger.warning(f"No transcripts found for encounter {encounter_id}")
            return ""
            
        # ادغام متن‌ها
        full_text = " ".join(transcripts)
        
        # حذف تکرارها در نقاط اتصال
        # TODO: پیاده‌سازی الگوریتم حذف تکرار
        cleaned_text = full_text
        
        # ذخیره متن کامل
        encounter = Encounter.objects.get(id=encounter_id)
        encounter.metadata['full_transcript'] = cleaned_text
        encounter.metadata['transcript_word_count'] = len(cleaned_text.split())
        encounter.metadata['transcript_merged_at'] = timezone.now().isoformat()
        encounter.save()
        
        logger.info(f"Transcripts merged for encounter {encounter_id}")
        
        # شروع تولید SOAP
        generate_soap_report_async.delay(encounter_id)
        
        return cleaned_text
        
    except Encounter.DoesNotExist:
        logger.error(f"Encounter {encounter_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error merging transcripts for encounter {encounter_id}: {str(e)}")
        raise


@shared_task(queue='nlp')
def generate_soap_report_async(encounter_id: str) -> Dict:
    """تولید گزارش SOAP به صورت async
    
    Args:
        encounter_id: شناسه ملاقات
        
    Returns:
        اطلاعات گزارش تولید شده
    """
    try:
        logger.info(f"Starting SOAP generation for encounter {encounter_id}")
        
        # استفاده از asyncio برای فراخوانی سرویس async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        soap_service = SOAPGenerationService()
        report = loop.run_until_complete(
            soap_service.generate_soap_report(encounter_id)
        )
        
        logger.info(f"SOAP report generated for encounter {encounter_id}")
        
        # ارسال نوتیفیکیشن به پزشک
        notify_doctor_soap_ready.delay(encounter_id, str(report.id))
        
        return {
            'encounter_id': encounter_id,
            'report_id': str(report.id),
            'is_complete': report.is_complete,
            'ai_confidence': report.ai_confidence
        }
        
    except Exception as e:
        logger.error(f"Error generating SOAP for encounter {encounter_id}: {str(e)}")
        raise


@shared_task
def process_encounter_audio_complete(encounter_id: str):
    """پردازش کامل صوت یک ملاقات
    
    این task زنجیره‌ای از taskها را اجرا می‌کند:
    1. ادغام قطعات صوتی
    2. ادغام رونویسی‌ها
    3. تولید گزارش SOAP
    """
    try:
        encounter = Encounter.objects.get(id=encounter_id)
        
        # بررسی تکمیل بودن همه قطعات
        total_chunks = encounter.audio_chunks.count()
        processed_chunks = encounter.audio_chunks.filter(is_processed=True).count()
        
        if total_chunks == 0:
            logger.warning(f"No audio chunks for encounter {encounter_id}")
            return
            
        if processed_chunks < total_chunks:
            logger.info(f"Not all chunks processed for encounter {encounter_id}: {processed_chunks}/{total_chunks}")
            return
            
        # ادغام صوت
        merge_audio_files.delay(encounter_id)
        
        # ادغام رونویسی‌ها و تولید SOAP
        chain(
            merge_encounter_transcripts.s(encounter_id),
            generate_post_visit_report.s(encounter_id)
        ).apply_async()
        
        logger.info(f"Post-visit processing started for encounter {encounter_id}")
        
    except Encounter.DoesNotExist:
        logger.error(f"Encounter {encounter_id} not found")
    except Exception as e:
        logger.error(f"Error in post-visit processing for encounter {encounter_id}: {str(e)}")


@shared_task
def merge_audio_files(encounter_id: str) -> Optional[str]:
    """ادغام فایل‌های صوتی یک ملاقات
    
    Args:
        encounter_id: شناسه ملاقات
        
    Returns:
        URL فایل ادغام شده
    """
    try:
        logger.info(f"Starting audio merge for encounter {encounter_id}")
        
        # استفاده از asyncio برای سرویس async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        audio_service = AudioProcessingService()
        merged_url = loop.run_until_complete(
            audio_service.merge_audio_chunks(encounter_id)
        )
        
        # به‌روزرسانی encounter
        encounter = Encounter.objects.get(id=encounter_id)
        encounter.recording_url = merged_url
        encounter.metadata['audio_merged_at'] = timezone.now().isoformat()
        encounter.save()
        
        logger.info(f"Audio merged for encounter {encounter_id}: {merged_url}")
        
        return merged_url
        
    except Exception as e:
        logger.error(f"Error merging audio for encounter {encounter_id}: {str(e)}")
        raise


@shared_task
def generate_post_visit_report(transcript_text: str, encounter_id: str):
    """تولید گزارش‌های پس از ویزیت
    
    شامل:
    - گزارش SOAP
    - خلاصه ویزیت برای بیمار
    - یادآوری‌های پیگیری
    """
    try:
        encounter = Encounter.objects.get(id=encounter_id)
        
        # تولید PDF گزارش SOAP
        if hasattr(encounter, 'soap_report'):
            generate_soap_pdf.delay(str(encounter.soap_report.id))
            
        # تولید خلاصه برای بیمار
        generate_patient_summary.delay(encounter_id)
        
        # تنظیم یادآوری‌های پیگیری
        if hasattr(encounter, 'soap_report') and encounter.soap_report.follow_up:
            schedule_follow_up_reminders.delay(encounter_id)
            
        logger.info(f"Post-visit reports queued for encounter {encounter_id}")
        
    except Encounter.DoesNotExist:
        logger.error(f"Encounter {encounter_id} not found")
    except Exception as e:
        logger.error(f"Error generating post-visit reports for encounter {encounter_id}: {str(e)}")


@shared_task
def generate_soap_pdf(report_id: str) -> Optional[str]:
    """تولید PDF از گزارش SOAP
    
    Args:
        report_id: شناسه گزارش
        
    Returns:
        URL فایل PDF
    """
    try:
        report = SOAPReport.objects.select_related('encounter').get(id=report_id)
        
        # TODO: اتصال به سرویس تولید PDF
        # فعلاً URL ساختگی
        pdf_url = f"https://storage.helssa.ir/reports/{report_id}/soap.pdf"
        
        report.pdf_url = pdf_url
        report.save()
        
        logger.info(f"PDF generated for SOAP report {report_id}")
        
        return pdf_url
        
    except SOAPReport.DoesNotExist:
        logger.error(f"SOAP report {report_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error generating PDF for report {report_id}: {str(e)}")
        raise


@shared_task
def generate_patient_summary(encounter_id: str):
    """تولید خلاصه ویزیت برای بیمار"""
    try:
        encounter = Encounter.objects.get(id=encounter_id)
        
        # TODO: تولید خلاصه ساده برای بیمار
        summary = {
            'visit_date': encounter.scheduled_at.isoformat(),
            'doctor': 'دکتر ...',  # TODO: از UnifiedUser
            'chief_complaint': encounter.chief_complaint,
            'key_points': [],
            'medications': [],
            'next_steps': []
        }
        
        # ذخیره در metadata
        encounter.metadata['patient_summary'] = summary
        encounter.save()
        
        # ارسال به بیمار
        notify_patient_summary_ready.delay(encounter_id)
        
        logger.info(f"Patient summary generated for encounter {encounter_id}")
        
    except Encounter.DoesNotExist:
        logger.error(f"Encounter {encounter_id} not found")
    except Exception as e:
        logger.error(f"Error generating patient summary for encounter {encounter_id}: {str(e)}")


@shared_task
def schedule_follow_up_reminders(encounter_id: str):
    """تنظیم یادآوری‌های پیگیری"""
    try:
        encounter = Encounter.objects.get(id=encounter_id)
        
        if not hasattr(encounter, 'soap_report'):
            return
            
        follow_up = encounter.soap_report.follow_up
        if not follow_up or not follow_up.get('date'):
            return
            
        # TODO: ایجاد task برای یادآوری در زمان مناسب
        logger.info(f"Follow-up reminders scheduled for encounter {encounter_id}")
        
    except Encounter.DoesNotExist:
        logger.error(f"Encounter {encounter_id} not found")
    except Exception as e:
        logger.error(f"Error scheduling follow-up reminders for encounter {encounter_id}: {str(e)}")


# Notification tasks

@shared_task
def notify_doctor_soap_ready(encounter_id: str, report_id: str):
    """اطلاع به پزشک از آماده شدن گزارش SOAP"""
    # TODO: ارسال نوتیفیکیشن
    logger.info(f"Doctor notified about SOAP report {report_id} for encounter {encounter_id}")


@shared_task
def notify_patient_summary_ready(encounter_id: str):
    """اطلاع به بیمار از آماده شدن خلاصه"""
    # TODO: ارسال نوتیفیکیشن
    logger.info(f"Patient notified about summary for encounter {encounter_id}")


# Periodic tasks

@shared_task
def cleanup_expired_prescriptions():
    """پاکسازی نسخه‌های منقضی شده"""
    from datetime import timedelta
    
    expiry_date = timezone.now() - timedelta(days=30)  # 30 روز پس از انقضا
    
    expired_prescriptions = Prescription.objects.filter(
        expires_at__lt=expiry_date,
        status='issued'  # فقط نسخه‌های صادر شده و تحویل نشده
    )
    
    count = expired_prescriptions.count()
    
    # TODO: آرشیو قبل از حذف
    
    expired_prescriptions.delete()
    
    logger.info(f"Cleaned up {count} expired prescriptions")
    
    return count


@shared_task
def check_encounter_recordings():
    """بررسی وضعیت ضبط ملاقات‌های در حال انجام"""
    
    # ملاقات‌های در حال انجام با ضبط فعال
    active_encounters = Encounter.objects.filter(
        status='in_progress',
        is_recording_enabled=True,
        recording_consent=True
    )
    
    for encounter in active_encounters:
        # بررسی وضعیت ضبط
        # TODO: اتصال به سرویس ویدیو
        logger.info(f"Checking recording status for encounter {encounter.id}")
        
    return active_encounters.count()