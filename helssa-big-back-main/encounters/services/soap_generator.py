from typing import Dict, List, Optional
import asyncio
from asgiref.sync import sync_to_async
from django.utils import timezone

from ..models import Encounter, SOAPReport, Transcript


class SOAPGenerationService:
    """سرویس تولید گزارش SOAP"""
    
    def __init__(self):
        self.ai_service = None  # TODO: اتصال به UnifiedAIService
        
    async def generate_soap_report(
        self,
        encounter_id: str,
        regenerate: bool = False
    ) -> SOAPReport:
        """تولید گزارش SOAP از ملاقات"""
        
        encounter = await sync_to_async(
            Encounter.objects.select_related('patient', 'doctor').get
        )(id=encounter_id)
        
        # بررسی وجود گزارش قبلی
        if not regenerate:
            existing_report = await sync_to_async(
                SOAPReport.objects.filter(
                    encounter=encounter,
                    doctor_approved=True
                ).first
            )()
            
            if existing_report:
                return existing_report
                
        # جمع‌آوری داده‌ها
        context = await self._prepare_context(encounter)
        
        # تولید بخش‌های SOAP
        soap_sections = await asyncio.gather(
            self._generate_subjective(context),
            self._generate_objective(context),
            self._generate_assessment(context),
            self._generate_plan(context)
        )
        
        # ترکیب و اعتبارسنجی
        soap_data = {
            'subjective': soap_sections[0],
            'objective': soap_sections[1],
            'assessment': soap_sections[2],
            'plan': soap_sections[3]
        }
        
        # اعتبارسنجی
        validation_result = await self._validate_soap(soap_data)
        if not validation_result['is_valid']:
            # تلاش برای اصلاح خودکار
            soap_data = await self._auto_correct_soap(
                soap_data,
                validation_result['issues']
            )
            
        # استخراج داده‌های ساختاریافته
        structured_data = await self._extract_structured_data(soap_data)
        
        # ایجاد یا به‌روزرسانی گزارش
        report, created = await sync_to_async(
            SOAPReport.objects.update_or_create
        )(
            encounter=encounter,
            defaults={
                **soap_data,
                **structured_data,
                'generation_method': 'ai',
                'ai_confidence': validation_result.get('confidence', 0.85)
            }
        )
        
        # تولید خروجی‌ها
        await self._generate_outputs(report)
        
        return report
        
    async def _prepare_context(self, encounter: Encounter) -> Dict:
        """آماده‌سازی context برای تولید SOAP"""
        
        # رونویسی کامل
        full_transcript = encounter.metadata.get('full_transcript', '')
        
        # اگر رونویسی کامل موجود نیست، از قطعات بسازیم
        if not full_transcript:
            transcripts = await sync_to_async(list)(
                Transcript.objects.filter(
                    audio_chunk__encounter=encounter
                ).order_by('audio_chunk__chunk_index').values_list('text', flat=True)
            )
            full_transcript = ' '.join(transcripts)
            
        # تاریخچه پزشکی بیمار
        patient_history = await self._get_patient_history(
            encounter.patient_id
        )
        
        # داروهای فعلی
        current_medications = await self._get_current_medications(
            encounter.patient_id
        )
        
        # نتایج آزمایشات اخیر
        recent_labs = await self._get_recent_lab_results(
            encounter.patient_id
        )
        
        # محاسبه سن بیمار
        patient_age = await self._calculate_patient_age(encounter.patient_id)
        
        return {
            'encounter': encounter,
            'transcript': full_transcript,
            'chief_complaint': encounter.chief_complaint,
            'patient': {
                'age': patient_age,
                'gender': await self._get_patient_gender(encounter.patient_id),
                'history': patient_history,
                'medications': current_medications,
                'labs': recent_labs
            },
            'visit_type': encounter.type,
            'duration': encounter.actual_duration.total_seconds() / 60 if encounter.actual_duration else encounter.duration_minutes
        }
        
    async def _generate_subjective(self, context: Dict) -> str:
        """تولید بخش Subjective"""
        
        # اگر AI service موجود نیست، متن پیش‌فرض
        if not self.ai_service:
            return self._generate_default_subjective(context)
            
        prompt = self._create_subjective_prompt(context)
        
        # TODO: ارسال به AI service
        response = "بخش Subjective تولید شده توسط AI"
        
        return response
        
    async def _generate_objective(self, context: Dict) -> str:
        """تولید بخش Objective"""
        
        # جمع‌آوری داده‌های عینی
        vital_signs = await self._extract_vital_signs(context['transcript'])
        exam_findings = await self._extract_exam_findings(context['transcript'])
        
        if not self.ai_service:
            return self._generate_default_objective(vital_signs, exam_findings)
            
        prompt = self._create_objective_prompt(context, vital_signs, exam_findings)
        
        # TODO: ارسال به AI service
        response = "بخش Objective تولید شده توسط AI"
        
        return response
        
    async def _generate_assessment(self, context: Dict) -> str:
        """تولید بخش Assessment"""
        
        # استخراج تشخیص‌های احتمالی
        possible_diagnoses = await self._extract_diagnoses(
            context['transcript']
        )
        
        if not self.ai_service:
            return self._generate_default_assessment(context, possible_diagnoses)
            
        prompt = self._create_assessment_prompt(context, possible_diagnoses)
        
        # TODO: ارسال به AI service
        response = "بخش Assessment تولید شده توسط AI"
        
        return response
        
    async def _generate_plan(self, context: Dict) -> str:
        """تولید بخش Plan"""
        
        if not self.ai_service:
            return self._generate_default_plan(context)
            
        prompt = self._create_plan_prompt(context)
        
        # TODO: ارسال به AI service
        response = "بخش Plan تولید شده توسط AI"
        
        return response
        
    async def _extract_structured_data(self, soap_data: Dict) -> Dict:
        """استخراج داده‌های ساختاریافته از SOAP"""
        
        # استخراج تشخیص‌ها با کد ICD
        diagnoses = await self._extract_icd_codes(soap_data['assessment'])
        
        # استخراج داروها
        medications = await self._parse_medications(soap_data['plan'])
        
        # استخراج آزمایشات
        lab_orders = await self._parse_lab_orders(soap_data['plan'])
        
        # استخراج برنامه پیگیری
        follow_up = await self._parse_follow_up(soap_data['plan'])
        
        return {
            'diagnoses': diagnoses,
            'medications': medications,
            'lab_orders': lab_orders,
            'follow_up': follow_up
        }
        
    async def _validate_soap(self, soap_data: Dict) -> Dict:
        """اعتبارسنجی گزارش SOAP"""
        
        issues = []
        
        # بررسی طول حداقلی بخش‌ها
        min_lengths = {
            'subjective': 50,
            'objective': 30,
            'assessment': 40,
            'plan': 30
        }
        
        for section, min_length in min_lengths.items():
            if len(soap_data.get(section, '')) < min_length:
                issues.append(f"بخش {section} خیلی کوتاه است")
                
        # بررسی وجود کلمات کلیدی
        if 'شکایت' not in soap_data.get('subjective', ''):
            issues.append("شکایت اصلی در بخش Subjective یافت نشد")
            
        confidence = 1.0 - (len(issues) * 0.1)
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'confidence': max(0.5, confidence)
        }
        
    async def _auto_correct_soap(
        self,
        soap_data: Dict,
        issues: List[str]
    ) -> Dict:
        """اصلاح خودکار مشکلات SOAP"""
        
        # TODO: پیاده‌سازی منطق اصلاح خودکار
        return soap_data
        
    async def _generate_outputs(self, report: SOAPReport):
        """تولید خروجی‌های گزارش"""
        
        # تولید محتوای Markdown
        markdown_content = await self._generate_markdown(report)
        report.markdown_content = markdown_content
        
        # TODO: تولید PDF
        # pdf_url = await self._generate_pdf(report)
        # report.pdf_url = pdf_url
        
        await sync_to_async(report.save)()
        
    async def _generate_markdown(self, report: SOAPReport) -> str:
        """تولید Markdown از گزارش SOAP"""
        
        encounter = report.encounter
        
        markdown_content = f"""# گزارش ملاقات پزشکی

## اطلاعات ویزیت
- **تاریخ**: {encounter.scheduled_at.strftime('%Y/%m/%d')}
- **نوع ویزیت**: {encounter.get_type_display()}
- **شکایت اصلی**: {encounter.chief_complaint}

## گزارش SOAP

### Subjective (شرح حال)
{report.subjective}

### Objective (معاینه)
{report.objective}

### Assessment (ارزیابی)
{report.assessment}

### Plan (برنامه درمان)
{report.plan}
"""
        
        # افزودن نسخه در صورت وجود
        if report.medications:
            markdown_content += "\n## نسخه پزشکی\n\n"
            for i, med in enumerate(report.medications, 1):
                markdown_content += f"{i}. **{med.get('name', '')}**\n"
                markdown_content += f"   - دوز: {med.get('dosage', '')}\n"
                markdown_content += f"   - روش مصرف: {med.get('route', '')}\n"
                markdown_content += f"   - مدت: {med.get('duration', '')}\n\n"
                
        return markdown_content
        
    # متدهای کمکی برای تولید محتوای پیش‌فرض
    
    def _generate_default_subjective(self, context: Dict) -> str:
        """تولید Subjective پیش‌فرض"""
        return f"""
شکایت اصلی: {context['chief_complaint']}

بیمار {context['patient']['age']} ساله با شکایت فوق مراجعه نموده است.
شرح حال بیماری فعلی نیاز به تکمیل دارد.
سابقه پزشکی: در حال بررسی
داروهای مصرفی: در حال بررسی
آلرژی: نامشخص
"""
        
    def _generate_default_objective(
        self,
        vital_signs: Dict,
        exam_findings: List[str]
    ) -> str:
        """تولید Objective پیش‌فرض"""
        return f"""
علائم حیاتی: در محدوده طبیعی
ظاهر عمومی: هوشیار، در وضعیت عمومی خوب
معاینه فیزیکی: نیاز به تکمیل دارد

یافته‌های معاینه:
{chr(10).join(f"- {finding}" for finding in exam_findings) if exam_findings else "- در حال بررسی"}
"""
        
    def _generate_default_assessment(
        self,
        context: Dict,
        diagnoses: List[str]
    ) -> str:
        """تولید Assessment پیش‌فرض"""
        return f"""
بیمار {context['patient']['age']} ساله با شکایت {context['chief_complaint']}

تشخیص‌های احتمالی:
{chr(10).join(f"- {d}" for d in diagnoses) if diagnoses else "- نیاز به بررسی بیشتر"}

ارزیابی نهایی نیاز به تکمیل دارد.
"""
        
    def _generate_default_plan(self, context: Dict) -> str:
        """تولید Plan پیش‌فرض"""
        return """
1. توصیه‌های عمومی ارائه شد
2. پیگیری در صورت عدم بهبودی
3. مراجعه فوری در صورت بروز علائم هشداردهنده

برنامه درمان نیاز به تکمیل دارد.
"""
        
    # متدهای کمکی برای استخراج اطلاعات
    
    async def _extract_vital_signs(self, transcript: str) -> Dict:
        """استخراج علائم حیاتی از رونویسی"""
        # TODO: پیاده‌سازی با regex یا NLP
        return {}
        
    async def _extract_exam_findings(self, transcript: str) -> List[str]:
        """استخراج یافته‌های معاینه"""
        # TODO: پیاده‌سازی با NLP
        return []
        
    async def _extract_diagnoses(self, transcript: str) -> List[str]:
        """استخراج تشخیص‌های احتمالی"""
        # TODO: پیاده‌سازی با NLP
        return []
        
    async def _extract_icd_codes(self, assessment: str) -> List[Dict]:
        """استخراج کدهای ICD"""
        # TODO: اتصال به دیتابیس ICD
        return []
        
    async def _parse_medications(self, plan: str) -> List[Dict]:
        """استخراج داروها از plan"""
        # TODO: پیاده‌سازی parser
        return []
        
    async def _parse_lab_orders(self, plan: str) -> List[Dict]:
        """استخراج دستورات آزمایش"""
        # TODO: پیاده‌سازی parser
        return []
        
    async def _parse_follow_up(self, plan: str) -> Dict:
        """استخراج برنامه پیگیری"""
        # TODO: پیاده‌سازی parser
        return {}
        
    # متدهای دریافت اطلاعات بیمار
    
    async def _get_patient_history(self, patient_id: str) -> List[Dict]:
        """دریافت تاریخچه پزشکی بیمار"""
        # TODO: اتصال به PatientProfile
        return []
        
    async def _get_current_medications(self, patient_id: str) -> List[Dict]:
        """دریافت داروهای فعلی بیمار"""
        # TODO: اتصال به Prescription model
        return []
        
    async def _get_recent_lab_results(self, patient_id: str) -> List[Dict]:
        """دریافت نتایج آزمایشات اخیر"""
        # TODO: اتصال به Lab Results
        return []
        
    async def _calculate_patient_age(self, patient_id: str) -> int:
        """محاسبه سن بیمار"""
        # TODO: دریافت از UnifiedUser
        return 30  # مقدار پیش‌فرض
        
    async def _get_patient_gender(self, patient_id: str) -> str:
        """دریافت جنسیت بیمار"""
        # TODO: دریافت از UnifiedUser
        return "نامشخص"
        
    # متدهای ایجاد prompt
    
    def _create_subjective_prompt(self, context: Dict) -> str:
        """ایجاد prompt برای Subjective"""
        return f"""
بر اساس رونویسی ملاقات پزشکی زیر، بخش Subjective گزارش SOAP را تولید کنید.

اطلاعات بیمار:
- سن: {context['patient']['age']} سال
- جنسیت: {context['patient']['gender']}
- شکایت اصلی: {context['chief_complaint']}

رونویسی ملاقات:
{context['transcript'][:3000]}

بخش Subjective باید شامل موارد زیر باشد:
1. شکایت اصلی (Chief Complaint - CC)
2. تاریخچه بیماری فعلی (History of Present Illness - HPI)
3. سابقه پزشکی (Past Medical History - PMH)
4. داروهای مصرفی (Medications)
5. آلرژی‌ها (Allergies)
"""
        
    def _create_objective_prompt(
        self,
        context: Dict,
        vital_signs: Dict,
        exam_findings: List[str]
    ) -> str:
        """ایجاد prompt برای Objective"""
        return f"""
بخش Objective گزارش SOAP را بر اساس اطلاعات زیر تولید کنید:

علائم حیاتی یافت شده:
{vital_signs}

یافته‌های معاینه:
{exam_findings}

بخش Objective باید شامل:
1. علائم حیاتی (Vital Signs)
2. ظاهر عمومی (General Appearance)
3. یافته‌های معاینه فیزیکی
4. نتایج آزمایشات و تصویربرداری
"""
        
    def _create_assessment_prompt(
        self,
        context: Dict,
        diagnoses: List[str]
    ) -> str:
        """ایجاد prompt برای Assessment"""
        return f"""
بخش Assessment گزارش SOAP را تولید کنید.

بر اساس:
- شکایت اصلی: {context['chief_complaint']}
- تشخیص‌های احتمالی: {diagnoses}

Assessment باید شامل:
1. خلاصه‌ای از وضعیت بیمار
2. تشخیص‌های احتمالی
3. تشخیص‌های افتراقی
4. ارزیابی شدت و پیش‌آگهی
"""
        
    def _create_plan_prompt(self, context: Dict) -> str:
        """ایجاد prompt برای Plan"""
        return """
بخش Plan گزارش SOAP را تولید کنید.

Plan باید شامل:
1. درمان دارویی
2. درمان‌های غیردارویی
3. آزمایشات و تصویربرداری‌های درخواستی
4. ارجاعات تخصصی
5. آموزش بیمار
6. زمان پیگیری
7. علائم هشداردهنده
"""