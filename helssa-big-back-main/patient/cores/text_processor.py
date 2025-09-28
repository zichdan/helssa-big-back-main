"""
هسته Text Processor برای سیستم مدیریت بیماران
Patient Management Text Processing Core
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from django.utils.text import slugify
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PatientTextProcessor:
    """
    هسته پردازش متن برای مدیریت اطلاعات بیماران
    Text processing core for patient information management
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
        self.english_numbers = '0123456789'
        
        # الگوهای regex برای استخراج اطلاعات
        self.patterns = {
            'national_code': re.compile(r'\b\d{10}\b'),
            'phone_number': re.compile(r'\b09\d{9}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'postal_code': re.compile(r'\b\d{10}\b'),
            'medicine_dosage': re.compile(r'\d+\s*(mg|gr|ml|cc|قرص|کپسول|میلی\s*گرم)', re.IGNORECASE),
            'date_persian': re.compile(r'\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b'),
            'time': re.compile(r'\b\d{1,2}:\d{2}(?::\d{2})?\b'),
            'blood_pressure': re.compile(r'\b\d{2,3}/\d{2,3}\b'),
            'temperature': re.compile(r'\b\d{2,3}\.?\d?\s*درجه|°C\b', re.IGNORECASE),
            'weight': re.compile(r'\b\d{2,3}\.?\d?\s*(kg|کیلو|کیلوگرم)\b', re.IGNORECASE),
            'height': re.compile(r'\b\d{2,3}\.?\d?\s*(cm|سانتی\s*متر)\b', re.IGNORECASE)
        }
        
        # کلمات کلیدی پزشکی
        self.medical_keywords = {
            'symptoms': [
                'درد', 'تب', 'سردرد', 'تهوع', 'استفراغ', 'اسهال', 'یبوست',
                'خستگی', 'ضعف', 'تنگی نفس', 'سرفه', 'عطسه', 'گلودرد'
            ],
            'body_parts': [
                'سر', 'گردن', 'سینه', 'شکم', 'پشت', 'دست', 'پا', 'زانو',
                'آرنج', 'مچ دست', 'انگشت', 'چشم', 'گوش', 'بینی', 'دهان'
            ],
            'medications': [
                'قرص', 'کپسول', 'شربت', 'آمپول', 'پماد', 'قطره', 'اسپری'
            ],
            'medical_tests': [
                'آزمایش خون', 'ادرار', 'رادیولوژی', 'سونوگرافی', 'سی تی اسکن',
                'ام آر آی', 'اکوکاردیوگرافی', 'الکتروکاردیوگرام'
            ]
        }
    
    async def process_patient_text(
        self,
        text: str,
        processing_type: str = 'general'
    ) -> Dict[str, Any]:
        """
        پردازش متن مرتبط با بیمار
        Process patient-related text
        
        Args:
            text: متن ورودی
            processing_type: نوع پردازش (general, medical_record, prescription, etc.)
            
        Returns:
            Dict: اطلاعات پردازش شده
        """
        try:
            # تمیز کردن و نرمال‌سازی متن
            cleaned_text = await self._clean_and_normalize_text(text)
            
            # استخراج اطلاعات ساختاریافته
            extracted_data = await self._extract_structured_data(cleaned_text)
            
            # تحلیل محتوای پزشکی
            medical_analysis = await self._analyze_medical_content(cleaned_text)
            
            # پردازش خاص بر اساس نوع
            specific_processing = await self._apply_specific_processing(
                cleaned_text, processing_type
            )
            
            # تولید خلاصه
            summary = await self._generate_text_summary(cleaned_text)
            
            return {
                'original_text': text,
                'cleaned_text': cleaned_text,
                'extracted_data': extracted_data,
                'medical_analysis': medical_analysis,
                'specific_processing': specific_processing,
                'summary': summary,
                'processing_metadata': {
                    'type': processing_type,
                    'text_length': len(text),
                    'cleaned_length': len(cleaned_text),
                    'confidence_score': self._calculate_confidence_score(extracted_data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Text processing error: {str(e)}")
            return {
                'error': str(e),
                'original_text': text,
                'cleaned_text': text
            }
    
    async def extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """
        استخراج موجودیت‌های پزشکی از متن
        Extract medical entities from text
        """
        try:
            entities = {
                'symptoms': [],
                'medications': [],
                'body_parts': [],
                'dosages': [],
                'vital_signs': [],
                'dates': [],
                'tests': []
            }
            
            text_lower = text.lower()
            
            # استخراج علائم
            for symptom in self.medical_keywords['symptoms']:
                if symptom in text_lower:
                    entities['symptoms'].append(symptom)
            
            # استخراج قسمت‌های بدن
            for body_part in self.medical_keywords['body_parts']:
                if body_part in text_lower:
                    entities['body_parts'].append(body_part)
            
            # استخراج داروها
            medicine_matches = self.patterns['medicine_dosage'].findall(text)
            entities['dosages'] = list(set(medicine_matches))
            
            # استخراج علائم حیاتی
            bp_matches = self.patterns['blood_pressure'].findall(text)
            if bp_matches:
                entities['vital_signs'].extend([f"فشار خون: {bp}" for bp in bp_matches])
            
            temp_matches = self.patterns['temperature'].findall(text)
            if temp_matches:
                entities['vital_signs'].extend([f"دما: {temp}" for temp in temp_matches])
            
            # استخراج تاریخ‌ها
            date_matches = self.patterns['date_persian'].findall(text)
            entities['dates'] = list(set(date_matches))
            
            return entities
            
        except Exception as e:
            self.logger.error(f"Medical entity extraction error: {str(e)}")
            return {}
    
    async def standardize_prescription_text(self, text: str) -> Dict[str, Any]:
        """
        استانداردسازی متن نسخه پزشکی
        Standardize prescription text
        """
        try:
            # تمیز کردن متن
            cleaned_text = await self._clean_and_normalize_text(text)
            
            # استخراج اطلاعات نسخه
            prescription_data = {
                'medications': [],
                'dosages': [],
                'frequencies': [],
                'durations': [],
                'instructions': []
            }
            
            # تقسیم متن به خطوط (هر دارو معمولاً در یک خط)
            lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
            
            for line in lines:
                medication_info = await self._parse_medication_line(line)
                if medication_info:
                    prescription_data['medications'].append(medication_info)
            
            # استخراج دوزها
            dosage_matches = self.patterns['medicine_dosage'].findall(cleaned_text)
            prescription_data['dosages'] = list(set(dosage_matches))
            
            # شناسایی دفعات مصرف
            frequency_patterns = [
                r'روزی\s*(\d+)\s*بار',
                r'(\d+)\s*بار\s*در\s*روز',
                r'صبح\s*و\s*شب',
                r'ناشتا',
                r'بعد\s*از\s*غذا',
                r'قبل\s*از\s*غذا'
            ]
            
            for pattern in frequency_patterns:
                matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
                prescription_data['frequencies'].extend(matches)
            
            return {
                'standardized_text': cleaned_text,
                'prescription_data': prescription_data,
                'medication_count': len(prescription_data['medications']),
                'confidence_score': self._calculate_prescription_confidence(prescription_data)
            }
            
        except Exception as e:
            self.logger.error(f"Prescription standardization error: {str(e)}")
            return {
                'error': str(e),
                'standardized_text': text
            }
    
    async def generate_medical_summary(
        self,
        texts: List[str],
        summary_type: str = 'general'
    ) -> Dict[str, Any]:
        """
        تولید خلاصه پزشکی از چندین متن
        Generate medical summary from multiple texts
        """
        try:
            # ترکیب متن‌ها
            combined_text = '\n'.join(texts)
            
            # استخراج موجودیت‌های مهم
            entities = await self.extract_medical_entities(combined_text)
            
            # تحلیل روند
            trends = await self._analyze_medical_trends(texts)
            
            # تولید خلاصه بر اساس نوع
            if summary_type == 'symptoms':
                summary = await self._generate_symptom_summary(entities, trends)
            elif summary_type == 'medications':
                summary = await self._generate_medication_summary(entities, trends)
            elif summary_type == 'vital_signs':
                summary = await self._generate_vital_signs_summary(entities, trends)
            else:
                summary = await self._generate_general_medical_summary(entities, trends)
            
            return {
                'summary': summary,
                'entities': entities,
                'trends': trends,
                'source_count': len(texts),
                'summary_type': summary_type
            }
            
        except Exception as e:
            self.logger.error(f"Medical summary generation error: {str(e)}")
            return {
                'error': str(e),
                'summary': 'خطا در تولید خلاصه'
            }
    
    async def _clean_and_normalize_text(self, text: str) -> str:
        """
        تمیز کردن و نرمال‌سازی متن
        Clean and normalize text
        """
        if not text:
            return ""
        
        # حذف کاراکترهای اضافی
        text = re.sub(r'\s+', ' ', text.strip())
        
        # تبدیل اعداد فارسی به انگلیسی
        for persian, english in zip(self.persian_numbers, self.english_numbers):
            text = text.replace(persian, english)
        
        # استانداردسازی علائم نگارشی
        text = text.replace('ي', 'ی').replace('ك', 'ک')
        text = text.replace('‌', ' ')  # نیم‌فاصله به فاصله
        
        return text
    
    async def _extract_structured_data(self, text: str) -> Dict[str, List[str]]:
        """
        استخراج داده‌های ساختاریافته از متن
        Extract structured data from text
        """
        structured_data = {}
        
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                structured_data[pattern_name] = list(set(matches))
        
        return structured_data
    
    async def _analyze_medical_content(self, text: str) -> Dict[str, Any]:
        """
        تحلیل محتوای پزشکی متن
        Analyze medical content of text
        """
        analysis = {
            'medical_score': 0,
            'categories': [],
            'urgency_level': 'normal',
            'completeness_score': 0
        }
        
        text_lower = text.lower()
        
        # محاسبه امتیاز پزشکی
        medical_terms_found = 0
        total_medical_terms = sum(len(terms) for terms in self.medical_keywords.values())
        
        for category, terms in self.medical_keywords.items():
            found_terms = [term for term in terms if term in text_lower]
            if found_terms:
                analysis['categories'].append(category)
                medical_terms_found += len(found_terms)
        
        analysis['medical_score'] = (medical_terms_found / total_medical_terms) * 100
        
        # تشخیص سطح اورژانس
        urgency_keywords = ['فوری', 'اورژانس', 'شدید', 'حاد', 'درد شدید', 'تب بالا']
        if any(keyword in text_lower for keyword in urgency_keywords):
            analysis['urgency_level'] = 'high'
        elif any(keyword in text_lower for keyword in ['خفیف', 'کم', 'بهتر']):
            analysis['urgency_level'] = 'low'
        
        # محاسبه امتیاز کامل بودن
        essential_elements = ['symptom', 'duration', 'severity', 'location']
        found_elements = 0
        
        if any(symptom in text_lower for symptom in self.medical_keywords['symptoms']):
            found_elements += 1
        if any(body_part in text_lower for body_part in self.medical_keywords['body_parts']):
            found_elements += 1
        if re.search(r'\d+\s*(روز|هفته|ماه)', text_lower):
            found_elements += 1
        if any(severity in text_lower for severity in ['شدید', 'متوسط', 'خفیف']):
            found_elements += 1
        
        analysis['completeness_score'] = (found_elements / len(essential_elements)) * 100
        
        return analysis
    
    async def _apply_specific_processing(
        self,
        text: str,
        processing_type: str
    ) -> Dict[str, Any]:
        """
        اعمال پردازش خاص بر اساس نوع
        Apply specific processing based on type
        """
        if processing_type == 'medical_record':
            return await self._process_medical_record_text(text)
        elif processing_type == 'prescription':
            return await self.standardize_prescription_text(text)
        elif processing_type == 'complaint':
            return await self._process_chief_complaint(text)
        elif processing_type == 'consent':
            return await self._process_consent_text(text)
        else:
            return {'type': 'general', 'processed': True}
    
    async def _process_medical_record_text(self, text: str) -> Dict[str, Any]:
        """
        پردازش متن سابقه پزشکی
        Process medical record text
        """
        # استخراج تاریخ‌ها
        dates = self.patterns['date_persian'].findall(text)
        
        # شناسایی نوع سابقه
        record_type = 'other'
        if any(word in text.lower() for word in ['آلرژی', 'حساسیت']):
            record_type = 'allergy'
        elif any(word in text.lower() for word in ['دارو', 'قرص', 'کپسول']):
            record_type = 'medication'
        elif any(word in text.lower() for word in ['جراحی', 'عمل']):
            record_type = 'surgery'
        elif any(word in text.lower() for word in ['بیماری', 'سابقه']):
            record_type = 'illness'
        
        return {
            'record_type': record_type,
            'dates_found': dates,
            'chronic_indicators': self._find_chronic_indicators(text)
        }
    
    async def _process_chief_complaint(self, text: str) -> Dict[str, Any]:
        """
        پردازش شکایت اصلی
        Process chief complaint
        """
        # استخراج مدت زمان
        duration_pattern = re.compile(r'(\d+)\s*(روز|هفته|ماه|سال)')
        duration_matches = duration_pattern.findall(text.lower())
        
        # استخراج شدت
        severity = 'unknown'
        if any(word in text.lower() for word in ['شدید', 'زیاد', 'بد']):
            severity = 'severe'
        elif any(word in text.lower() for word in ['متوسط', 'نسبی']):
            severity = 'moderate'
        elif any(word in text.lower() for word in ['خفیف', 'کم', 'اندک']):
            severity = 'mild'
        
        return {
            'durations': duration_matches,
            'severity': severity,
            'pain_indicators': self._find_pain_indicators(text)
        }
    
    async def _process_consent_text(self, text: str) -> Dict[str, Any]:
        """
        پردازش متن رضایت‌نامه
        Process consent text
        """
        # شناسایی نوع رضایت‌نامه
        consent_type = 'general'
        if any(word in text.lower() for word in ['جراحی', 'عمل']):
            consent_type = 'surgery'
        elif any(word in text.lower() for word in ['درمان', 'دارو']):
            consent_type = 'treatment'
        elif any(word in text.lower() for word in ['ضبط', 'فیلم']):
            consent_type = 'recording'
        
        # بررسی کلمات کلیدی قانونی
        legal_terms = ['موافقت', 'رضایت', 'مسئولیت', 'خطر', 'عوارض']
        found_legal_terms = [term for term in legal_terms if term in text.lower()]
        
        return {
            'consent_type': consent_type,
            'legal_terms_found': found_legal_terms,
            'completeness_score': (len(found_legal_terms) / len(legal_terms)) * 100
        }
    
    async def _generate_text_summary(self, text: str) -> str:
        """
        تولید خلاصه متن
        Generate text summary
        """
        if len(text) <= 200:
            return text
        
        # تقسیم به جملات
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 3:
            return text
        
        # انتخاب مهم‌ترین جملات (ساده‌سازی شده)
        important_sentences = sentences[:2] + sentences[-1:]
        return '. '.join(important_sentences) + '.'
    
    async def _parse_medication_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        تجزیه خط دارو
        Parse medication line
        """
        # الگوی ساده برای تجزیه دارو
        # فرمت: نام دارو - دوز - دفعات - مدت
        parts = [part.strip() for part in line.split('-')]
        
        if len(parts) >= 2:
            return {
                'name': parts[0],
                'dosage': parts[1] if len(parts) > 1 else '',
                'frequency': parts[2] if len(parts) > 2 else '',
                'duration': parts[3] if len(parts) > 3 else ''
            }
        
        return None
    
    def _calculate_confidence_score(self, extracted_data: Dict[str, Any]) -> float:
        """
        محاسبه امتیاز اطمینان
        Calculate confidence score
        """
        if not extracted_data:
            return 0.0
        
        # امتیاز بر اساس تعداد داده‌های استخراج شده
        total_items = sum(len(items) if isinstance(items, list) else 1 
                         for items in extracted_data.values())
        
        # حداکثر امتیاز 100
        confidence = min(total_items * 10, 100)
        return round(confidence, 2)
    
    def _calculate_prescription_confidence(self, prescription_data: Dict[str, Any]) -> float:
        """
        محاسبه امتیاز اطمینان نسخه
        Calculate prescription confidence score
        """
        score = 0
        
        # دارو
        if prescription_data.get('medications'):
            score += 30
        
        # دوز
        if prescription_data.get('dosages'):
            score += 25
        
        # دفعات
        if prescription_data.get('frequencies'):
            score += 25
        
        # دستورات
        if prescription_data.get('instructions'):
            score += 20
        
        return min(score, 100)
    
    def _find_chronic_indicators(self, text: str) -> List[str]:
        """
        یافتن نشانگرهای بیماری مزمن
        Find chronic disease indicators
        """
        chronic_keywords = [
            'مزمن', 'طولانی مدت', 'چندین سال', 'همیشه',
            'دائمی', 'مستمر', 'مداوم'
        ]
        
        return [keyword for keyword in chronic_keywords if keyword in text.lower()]
    
    def _find_pain_indicators(self, text: str) -> Dict[str, Any]:
        """
        یافتن نشانگرهای درد
        Find pain indicators
        """
        pain_types = {
            'sharp': ['تیز', 'برنده'],
            'dull': ['کند', 'مبهم'],
            'throbbing': ['ضربان دار', 'تپش'],
            'burning': ['سوزشی', 'سوزش']
        }
        
        found_types = []
        for pain_type, keywords in pain_types.items():
            if any(keyword in text.lower() for keyword in keywords):
                found_types.append(pain_type)
        
        return {
            'types': found_types,
            'has_pain': 'درد' in text.lower()
        }
    
    async def _analyze_medical_trends(self, texts: List[str]) -> Dict[str, Any]:
        """
        تحلیل روند پزشکی
        Analyze medical trends
        """
        # این تابع می‌تواند برای تحلیل روند تغییرات در طول زمان استفاده شود
        return {
            'trend_analysis': 'basic',
            'text_count': len(texts),
            'average_length': sum(len(text) for text in texts) / len(texts) if texts else 0
        }
    
    async def _generate_symptom_summary(
        self, 
        entities: Dict[str, List[str]], 
        trends: Dict[str, Any]
    ) -> str:
        """
        تولید خلاصه علائم
        Generate symptoms summary
        """
        symptoms = entities.get('symptoms', [])
        if not symptoms:
            return "هیچ علامت خاصی شناسایی نشد."
        
        return f"علائم شناسایی شده: {', '.join(symptoms[:5])}"
    
    async def _generate_medication_summary(
        self, 
        entities: Dict[str, List[str]], 
        trends: Dict[str, Any]
    ) -> str:
        """
        تولید خلاصه داروها
        Generate medications summary
        """
        dosages = entities.get('dosages', [])
        if not dosages:
            return "اطلاعات دارویی خاصی شناسایی نشد."
        
        return f"داروهای شناسایی شده: {len(dosages)} مورد"
    
    async def _generate_vital_signs_summary(
        self, 
        entities: Dict[str, List[str]], 
        trends: Dict[str, Any]
    ) -> str:
        """
        تولید خلاصه علائم حیاتی
        Generate vital signs summary
        """
        vital_signs = entities.get('vital_signs', [])
        if not vital_signs:
            return "علائم حیاتی خاصی ثبت نشده."
        
        return f"علائم حیاتی: {', '.join(vital_signs[:3])}"
    
    async def _generate_general_medical_summary(
        self, 
        entities: Dict[str, List[str]], 
        trends: Dict[str, Any]
    ) -> str:
        """
        تولید خلاصه عمومی پزشکی
        Generate general medical summary
        """
        total_entities = sum(len(items) for items in entities.values())
        return f"در مجموع {total_entities} مورد اطلاعات پزشکی شناسایی شد."