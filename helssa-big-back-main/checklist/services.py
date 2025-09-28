"""
سرویس‌های اپلیکیشن Checklist برای ارزیابی چک‌لیست‌ها
"""
import re
import logging
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    ChecklistCatalog,
    ChecklistEval,
    ChecklistTemplate,
    ChecklistAlert
)

logger = logging.getLogger(__name__)
User = get_user_model()


class ChecklistEvaluationService:
    """
    سرویس برای ارزیابی آیتم‌های چک‌لیست در برابر متن ویزیت
    """
    
    def __init__(self):
        self.confidence_threshold = 0.6
    
    def evaluate_encounter(self, encounter_id: int, template_id: Optional[int] = None) -> Dict[str, Any]:
        """
        ارزیابی آیتم‌های چک‌لیست برای یک ویزیت
        
        Args:
            encounter_id: شناسه ویزیت برای ارزیابی
            template_id: شناسه قالب اختیاری برای استفاده از آیتم‌های خاص
        
        Returns:
            دیکشنری با نتایج ارزیابی
        """
        # Import داخلی برای جلوگیری از circular import
        from encounters.models import Encounter
        
        try:
            encounter = Encounter.objects.get(id=encounter_id)
        except Encounter.DoesNotExist:
            raise ValueError(f"ویزیت با شناسه {encounter_id} یافت نشد")
        
        # دریافت متن transcript
        transcript_text = self._get_encounter_transcript(encounter)
        if not transcript_text:
            logger.warning(f"متن transcript برای ویزیت {encounter_id} یافت نشد")
            return {'message': 'متن transcript برای ارزیابی موجود نیست'}
        
        # دریافت آیتم‌های چک‌لیست برای ارزیابی
        if template_id:
            try:
                template = ChecklistTemplate.objects.get(id=template_id)
                catalog_items = template.catalog_items.filter(is_active=True)
            except ChecklistTemplate.DoesNotExist:
                raise ValueError(f"قالب با شناسه {template_id} یافت نشد")
        else:
            # استفاده از همه آیتم‌های فعال کاتالوگ
            catalog_items = ChecklistCatalog.objects.filter(is_active=True)
        
        results = []
        
        with transaction.atomic():
            for item in catalog_items:
                evaluation = self._evaluate_catalog_item(encounter, item, transcript_text)
                results.append(evaluation)
            
            # ایجاد هشدارها بر اساس نتایج
            self._create_alerts_for_evaluations(encounter, results)
        
        return {
            'encounter_id': encounter_id,
            'evaluated_items': len(results),
            'results': results
        }
    
    def _get_encounter_transcript(self, encounter) -> str:
        """
        دریافت متن کامل transcript برای یک ویزیت
        """
        # دریافت همه بخش‌های transcript برای این ویزیت
        if hasattr(encounter, 'transcript_segments'):
            segments = encounter.transcript_segments.all().order_by('start_time')
            
            if not segments.exists():
                return ""
            
            # ترکیب همه متن‌های transcript
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text)
            
            return " ".join(transcript_parts)
        
        # اگر مدل transcript_segments وجود ندارد، متن خالی برگردان
        return ""
    
    def _evaluate_catalog_item(self, encounter, item: ChecklistCatalog, transcript_text: str) -> Dict[str, Any]:
        """
        ارزیابی یک آیتم کاتالوگ در برابر متن transcript
        
        Args:
            encounter: شیء ویزیت
            item: آیتم کاتالوگ برای ارزیابی
            transcript_text: متن کامل transcript
        
        Returns:
            دیکشنری با نتایج ارزیابی
        """
        # بررسی وجود ارزیابی قبلی
        eval_obj, created = ChecklistEval.objects.get_or_create(
            encounter=encounter,
            catalog_item=item,
            defaults={
                'status': 'unclear',
                'confidence_score': 0.0,
                'evidence_text': '',
                'anchor_positions': [],
                'generated_question': '',
                'notes': ''
            }
        )
        
        # انجام ارزیابی بر اساس کلمات کلیدی
        evaluation_result = self._keyword_based_evaluation(item, transcript_text)
        
        # به‌روزرسانی شیء ارزیابی
        eval_obj.status = evaluation_result['status']
        eval_obj.confidence_score = evaluation_result['confidence_score']
        eval_obj.evidence_text = evaluation_result['evidence_text']
        eval_obj.anchor_positions = evaluation_result['anchor_positions']
        eval_obj.generated_question = evaluation_result['generated_question']
        eval_obj.notes = evaluation_result['notes']
        eval_obj.save()
        
        return {
            'catalog_item_id': item.id,
            'catalog_item_title': item.title,
            'status': eval_obj.status,
            'confidence_score': eval_obj.confidence_score,
            'evidence_text': eval_obj.evidence_text,
            'generated_question': eval_obj.generated_question
        }
    
    def _keyword_based_evaluation(self, item: ChecklistCatalog, transcript_text: str) -> Dict[str, Any]:
        """
        ارزیابی بر اساس کلمات کلیدی
        
        Args:
            item: آیتم کاتالوگ
            transcript_text: متن کامل transcript
        
        Returns:
            دیکشنری با نتایج ارزیابی
        """
        keywords = item.keywords or []
        if not keywords:
            return {
                'status': 'unclear',
                'confidence_score': 0.0,
                'evidence_text': '',
                'anchor_positions': [],
                'generated_question': item.question_template,
                'notes': 'کلمات کلیدی برای ارزیابی تعریف نشده است'
            }
        
        # تبدیل متن به حروف کوچک برای مطابقت غیرحساس به حروف
        transcript_lower = transcript_text.lower()
        
        # یافتن مطابقت‌های کلمات کلیدی
        matches = []
        matched_keywords = []
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # استفاده از word boundaries برای جلوگیری از مطابقت‌های جزئی
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            
            for match in re.finditer(pattern, transcript_lower):
                matches.append({
                    'keyword': keyword,
                    'start': match.start(),
                    'end': match.end(),
                    'context': self._extract_context(transcript_text, match.start(), match.end())
                })
                matched_keywords.append(keyword)
        
        # محاسبه امتیاز اطمینان بر اساس پوشش کلمات کلیدی
        keyword_coverage = len(set(matched_keywords)) / len(keywords) if keywords else 0
        
        # تعیین وضعیت بر اساس مطابقت‌ها و اطمینان
        if not matches:
            status = 'missing'
            confidence_score = 0.0
        elif keyword_coverage >= 0.8:
            status = 'covered'
            confidence_score = min(0.9, keyword_coverage)
        elif keyword_coverage >= 0.5:
            status = 'partial'
            confidence_score = keyword_coverage * 0.8
        else:
            status = 'unclear'
            confidence_score = keyword_coverage * 0.6
        
        # استخراج متن شاهد از مطابقت‌ها
        evidence_parts = []
        anchor_positions = []
        
        for match in matches[:3]:  # محدود به ۳ مطابقت اول
            evidence_parts.append(match['context'])
            anchor_positions.append([match['start'], match['end']])
        
        evidence_text = " ... ".join(evidence_parts)
        
        # تولید سوال پیگیری در صورت نیاز
        generated_question = ""
        if status in ['missing', 'unclear', 'partial']:
            generated_question = item.question_template
        
        return {
            'status': status,
            'confidence_score': confidence_score,
            'evidence_text': evidence_text,
            'anchor_positions': anchor_positions,
            'generated_question': generated_question,
            'notes': f"پیدا شد {len(matches)} مطابقت کلمه کلیدی ({len(set(matched_keywords))}/{len(keywords)} کلمه منحصر به فرد)"
        }
    
    def _extract_context(self, text: str, start: int, end: int, context_length: int = 100) -> str:
        """
        استخراج متن اطراف یک مطابقت
        
        Args:
            text: متن کامل
            start: موقعیت شروع مطابقت
            end: موقعیت پایان مطابقت
            context_length: تعداد کاراکترهای اطراف برای نمایش
        
        Returns:
            رشته متن با context
        """
        # محاسبه محدوده context
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        
        # استخراج context
        context = text[context_start:context_end]
        
        # اضافه کردن ... اگر متن بریده شده
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."
        
        return context.strip()
    
    def _create_alerts_for_evaluations(self, encounter, evaluations: List[Dict[str, Any]]):
        """
        ایجاد هشدارها بر اساس نتایج ارزیابی
        
        Args:
            encounter: شیء ویزیت
            evaluations: لیست نتایج ارزیابی
        """
        for eval_result in evaluations:
            catalog_item = ChecklistCatalog.objects.get(id=eval_result['catalog_item_id'])
            
            # هشدار برای آیتم‌های بحرانی پوشش داده نشده
            if catalog_item.priority == 'critical' and eval_result['status'] in ['missing', 'unclear']:
                ChecklistAlert.objects.create(
                    encounter=encounter,
                    alert_type='missing_critical',
                    message=f"آیتم بحرانی '{catalog_item.title}' پوشش داده نشده است.",
                    created_by=encounter.created_by
                )
            
            # هشدار برای آیتم‌های با اطمینان پایین
            elif eval_result['confidence_score'] < 0.5 and eval_result['status'] != 'not_applicable':
                ChecklistAlert.objects.create(
                    encounter=encounter,
                    alert_type='low_confidence',
                    message=f"اطمینان پایین برای آیتم '{catalog_item.title}' (امتیاز: {eval_result['confidence_score']:.2f})",
                    created_by=encounter.created_by
                )
            
            # هشدار برای علائم خطر
            if catalog_item.category == 'red_flags' and eval_result['status'] == 'covered':
                ChecklistAlert.objects.create(
                    encounter=encounter,
                    alert_type='red_flag',
                    message=f"علامت خطر شناسایی شد: {catalog_item.title}",
                    created_by=encounter.created_by
                )


class ChecklistService:
    """
    سرویس اصلی برای مدیریت چک‌لیست‌ها
    """
    
    def __init__(self):
        self.evaluation_service = ChecklistEvaluationService()
    
    def create_instance(self, catalog_id: int, encounter_id: int) -> ChecklistEval:
        """
        ایجاد یک نمونه ChecklistEval برای کاتالوگ و ویزیت مشخص
        """
        from encounters.models import Encounter
        
        catalog = ChecklistCatalog.objects.get(id=catalog_id)
        encounter = Encounter.objects.get(id=encounter_id)
        
        instance, _ = ChecklistEval.objects.get_or_create(
            encounter=encounter,
            catalog_item=catalog,
            defaults={'status': 'missing', 'confidence_score': 0.0}
        )
        return instance
    
    def get_evaluation_summary(self, encounter_id: int) -> Dict[str, Any]:
        """
        دریافت خلاصه ارزیابی‌های چک‌لیست برای یک ویزیت
        
        Args:
            encounter_id: شناسه ویزیت
        
        Returns:
            دیکشنری با آمار خلاصه
        """
        evals = ChecklistEval.objects.filter(encounter_id=encounter_id)
        
        total_items = evals.count()
        if total_items == 0:
            return {
                'total_items': 0,
                'covered_items': 0,
                'missing_items': 0,
                'partial_items': 0,
                'unclear_items': 0,
                'coverage_percentage': 0.0,
                'needs_attention': 0,
                'active_alerts': 0
            }
        
        # شمارش بر اساس وضعیت
        status_counts = {}
        for eval_obj in evals:
            status = eval_obj.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        covered_items = status_counts.get('covered', 0)
        coverage_percentage = (covered_items / total_items) * 100
        
        # شمارش آیتم‌هایی که نیاز به توجه دارند
        needs_attention = evals.filter(
            status__in=['missing', 'unclear']
        ).count()
        
        # اضافه کردن آیتم‌های جزئی با اطمینان پایین
        needs_attention += evals.filter(
            status='partial',
            confidence_score__lt=0.7
        ).count()
        
        # شمارش هشدارهای فعال
        active_alerts = ChecklistAlert.objects.filter(
            encounter_id=encounter_id,
            is_dismissed=False
        ).count()
        
        return {
            'total_items': total_items,
            'covered_items': covered_items,
            'missing_items': status_counts.get('missing', 0),
            'partial_items': status_counts.get('partial', 0),
            'unclear_items': status_counts.get('unclear', 0),
            'coverage_percentage': round(coverage_percentage, 2),
            'needs_attention': needs_attention,
            'active_alerts': active_alerts
        }
    
    def get_pending_questions(self, encounter_id: int) -> List[Dict[str, Any]]:
        """
        دریافت سوالات در انتظار برای یک ویزیت
        
        Args:
            encounter_id: شناسه ویزیت
        
        Returns:
            لیست سوالات که نیاز به پاسخ دارند
        """
        evals = ChecklistEval.objects.filter(
            encounter_id=encounter_id,
            status__in=['missing', 'unclear', 'partial'],
            generated_question__isnull=False,
            doctor_response=''
        ).select_related('catalog_item')
        
        questions = []
        for eval_obj in evals:
            questions.append({
                'evaluation_id': eval_obj.id,
                'catalog_item_id': eval_obj.catalog_item.id,
                'catalog_item_title': eval_obj.catalog_item.title,
                'question': eval_obj.generated_question,
                'priority': eval_obj.catalog_item.priority,
                'category': eval_obj.catalog_item.category
            })
        
        # مرتب‌سازی بر اساس اولویت
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        questions.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return questions