"""
سرویس‌های تحلیل تریاژ پزشکی
Triage Analysis Services
"""

from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q, Count, Avg, Max
from django.utils import timezone
from django.core.cache import cache
import logging
import json
import re

from .models import (
    Symptom,
    DifferentialDiagnosis,
    TriageSession,
    SessionSymptom,
    SessionDiagnosis,
    TriageRule,
    DiagnosisSymptom
)

logger = logging.getLogger(__name__)


class TriageAnalysisService:
    """
    سرویس تحلیل و پردازش تریاژ پزشکی
    """
    
    def __init__(self):
        self.urgency_weights = {
            1: 0.1, 2: 0.2, 3: 0.4, 4: 0.7, 5: 1.0,
            6: 1.5, 7: 2.0, 8: 3.0, 9: 4.0, 10: 5.0
        }
        self.red_flag_symptoms = [
            'درد قفسه سینه', 'تنگی نفس شدید', 'از دست دادن هوشیاری',
            'خونریزی شدید', 'درد شکم حاد', 'تب بالای 39 درجه',
            'سردرد ناگهانی و شدید', 'اختلال بینایی ناگهانی'
        ]
    
    def analyze_initial_symptoms(self, session: TriageSession) -> Dict[str, Any]:
        """
        تحلیل اولیه علائم گزارش شده
        """
        try:
            symptoms_text = ' '.join(session.reported_symptoms)
            
            # شناسایی علائم از متن
            identified_symptoms = self._extract_symptoms_from_text(symptoms_text)
            
            # محاسبه سطح اورژانس اولیه
            urgency = self._calculate_initial_urgency(identified_symptoms)
            
            # شناسایی علائم خطر
            red_flags = self._detect_red_flags(symptoms_text, identified_symptoms)
            
            # به‌روزرسانی جلسه
            session.urgency_level = urgency
            session.red_flags_detected = red_flags
            session.requires_immediate_attention = bool(red_flags) or urgency >= 4
            session.ai_confidence_score = 0.7  # امتیاز اولیه
            session.save()
            
            return {
                'identified_symptoms': identified_symptoms,
                'urgency_level': urgency,
                'red_flags': red_flags,
                'requires_immediate_attention': session.requires_immediate_attention,
                'recommendations': self._get_initial_recommendations(urgency, red_flags)
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل اولیه علائم: {e}")
            raise
    
    def analyze_session_symptoms(self, session: TriageSession) -> Dict[str, Any]:
        """
        تحلیل علائم شناسایی شده در جلسه
        """
        try:
            # دریافت علائم جلسه
            session_symptoms = SessionSymptom.objects.filter(session=session)
            
            if not session_symptoms.exists():
                return {'message': 'هیچ علامتی یافت نشد'}
            
            # محاسبه امتیاز اورژانس
            urgency_score = self._calculate_symptom_urgency(session_symptoms)
            
            # پیدا کردن تشخیص‌های محتمل
            possible_diagnoses = self._find_differential_diagnoses(session_symptoms)
            
            # اعمال قوانین تریاژ
            applied_rules = self._apply_triage_rules(session, session_symptoms)
            
            # شناسایی علائم خطر جدید
            new_red_flags = self._detect_session_red_flags(session_symptoms)
            
            # به‌روزرسانی جلسه
            session.urgency_level = urgency_score
            session.red_flags_detected.extend(new_red_flags)
            session.requires_immediate_attention = urgency_score >= 4 or bool(new_red_flags)
            session.ai_confidence_score = self._calculate_confidence_score(session_symptoms, possible_diagnoses)
            session.save()
            
            # ذخیره تشخیص‌های محتمل
            self._save_session_diagnoses(session, possible_diagnoses)
            
            return {
                'urgency_score': urgency_score,
                'possible_diagnoses': possible_diagnoses,
                'applied_rules': applied_rules,
                'new_red_flags': new_red_flags,
                'confidence_score': session.ai_confidence_score,
                'recommendations': self._generate_recommendations(session, possible_diagnoses)
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل علائم جلسه: {e}")
            raise
    
    def complete_triage_analysis(self, session: TriageSession) -> Dict[str, Any]:
        """
        تحلیل نهایی تریاژ
        """
        try:
            # تحلیل نهایی علائم
            final_analysis = self.analyze_session_symptoms(session)
            
            # محاسبه زمان انتظار تخمینی
            estimated_wait = self._calculate_wait_time(session.urgency_level)
            
            # تولید اقدامات نهایی
            final_actions = self._generate_final_actions(session)
            
            # به‌روزرسانی اطلاعات نهایی
            session.estimated_wait_time = estimated_wait
            session.recommended_actions = final_actions
            session.save()
            
            return {
                **final_analysis,
                'estimated_wait_time_minutes': int(estimated_wait.total_seconds() // 60) if estimated_wait else None,
                'final_actions': final_actions,
                'summary': self._generate_session_summary(session)
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل نهایی تریاژ: {e}")
            raise
    
    def analyze_symptoms_standalone(
        self,
        symptoms: List[str],
        severity_scores: Dict[str, int] = None,
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
        medical_history: List[str] = None
    ) -> Dict[str, Any]:
        """
        تحلیل علائم بدون ایجاد جلسه
        """
        try:
            # یافتن علائم مطابق در دیتابیس
            matched_symptoms = self._match_symptoms_to_database(symptoms)
            
            # محاسبه امتیاز اورژانس
            urgency = self._calculate_standalone_urgency(
                matched_symptoms, severity_scores or {}
            )
            
            # پیدا کردن تشخیص‌های محتمل
            possible_diagnoses = self._find_diagnoses_for_symptoms(matched_symptoms)
            
            # اعمال فیلترهای سن و جنسیت
            if patient_age or patient_gender:
                possible_diagnoses = self._filter_diagnoses_by_demographics(
                    possible_diagnoses, patient_age, patient_gender
                )
            
            # شناسایی علائم خطر
            red_flags = self._detect_red_flags_from_symptoms(matched_symptoms)
            
            return {
                'matched_symptoms': [
                    {
                        'name': symptom.name,
                        'urgency_score': symptom.urgency_score,
                        'category': symptom.category.name
                    }
                    for symptom in matched_symptoms
                ],
                'urgency_level': urgency,
                'possible_diagnoses': possible_diagnoses[:5],  # تا 5 تشخیص اول
                'red_flags': red_flags,
                'requires_immediate_attention': urgency >= 4 or bool(red_flags),
                'recommendations': self._get_standalone_recommendations(urgency, red_flags),
                'confidence_score': self._calculate_standalone_confidence(matched_symptoms, possible_diagnoses)
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل مستقل علائم: {e}")
            raise
    
    def get_session_analysis(self, session: TriageSession) -> Dict[str, Any]:
        """
        دریافت تحلیل کامل جلسه
        """
        try:
            # اطلاعات پایه جلسه
            analysis = {
                'session_id': str(session.id),
                'status': session.status,
                'urgency_level': session.urgency_level,
                'duration_minutes': int(session.duration.total_seconds() // 60),
                'requires_immediate_attention': session.requires_immediate_attention,
                'confidence_score': session.ai_confidence_score
            }
            
            # علائم شناسایی شده
            session_symptoms = SessionSymptom.objects.filter(session=session)
            analysis['symptoms'] = [
                {
                    'name': ss.symptom.name,
                    'severity': ss.severity,
                    'duration_hours': ss.duration_hours,
                    'location': ss.location,
                    'urgency_score': ss.symptom.urgency_score
                }
                for ss in session_symptoms
            ]
            
            # تشخیص‌های احتمالی
            session_diagnoses = SessionDiagnosis.objects.filter(session=session)
            analysis['diagnoses'] = [
                {
                    'name': sd.diagnosis.name,
                    'probability_score': sd.probability_score,
                    'confidence_level': sd.confidence_level,
                    'urgency_level': sd.diagnosis.urgency_level,
                    'reasoning': sd.reasoning
                }
                for sd in session_diagnoses
            ]
            
            # علائم خطر
            analysis['red_flags'] = session.red_flags_detected
            
            # اقدامات توصیه شده
            analysis['recommended_actions'] = session.recommended_actions
            
            # زمان انتظار تخمینی
            if session.estimated_wait_time:
                analysis['estimated_wait_time_minutes'] = int(
                    session.estimated_wait_time.total_seconds() // 60
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"خطا در دریافت تحلیل جلسه: {e}")
            raise
    
    def _extract_symptoms_from_text(self, text: str) -> List[Symptom]:
        """
        استخراج علائم از متن
        """
        # الگوهای شایع برای علائم
        symptom_patterns = [
            r'درد\s+(\w+)',
            r'(\w+)\s+درد',
            r'تب\s*(?:دارم|کردم)?',
            r'سردرد',
            r'تهوع',
            r'استفراغ',
            r'سرگیجه',
            r'خستگی',
            r'ضعف'
        ]
        
        symptoms = []
        text_lower = text.lower()
        
        # جستجو در دیتابیس برای تطبیق نام‌ها
        for word in text.split():
            word_clean = re.sub(r'[^\w\s]', '', word).strip()
            if len(word_clean) >= 3:
                matching_symptoms = Symptom.objects.filter(
                    Q(name__icontains=word_clean) | Q(name_en__icontains=word_clean),
                    is_active=True
                )
                symptoms.extend(matching_symptoms)
        
        return list(set(symptoms))  # حذف تکراری‌ها
    
    def _calculate_initial_urgency(self, symptoms: List[Symptom]) -> int:
        """
        محاسبه سطح اورژانس اولیه
        """
        if not symptoms:
            return 1
        
        max_urgency = max(symptom.urgency_score for symptom in symptoms)
        avg_urgency = sum(symptom.urgency_score for symptom in symptoms) / len(symptoms)
        
        # تبدیل به مقیاس 1-5
        calculated_urgency = (max_urgency * 0.6 + avg_urgency * 0.4) / 2
        return min(int(calculated_urgency) + 1, 5)
    
    def _detect_red_flags(self, text: str, symptoms: List[Symptom]) -> List[str]:
        """
        شناسایی علائم خطر
        """
        red_flags = []
        text_lower = text.lower()
        
        # بررسی علائم خطر در متن
        for flag in self.red_flag_symptoms:
            if flag.lower() in text_lower:
                red_flags.append(flag)
        
        # بررسی علائم با امتیاز اورژانس بالا
        for symptom in symptoms:
            if symptom.urgency_score >= 8:
                red_flags.append(f"علامت اورژانسی: {symptom.name}")
        
        return red_flags
    
    def _calculate_symptom_urgency(self, session_symptoms) -> int:
        """
        محاسبه امتیاز اورژانس بر اساس علائم جلسه
        """
        if not session_symptoms.exists():
            return 1
        
        total_score = 0
        total_weight = 0
        
        for ss in session_symptoms:
            symptom_weight = self.urgency_weights.get(ss.symptom.urgency_score, 0.1)
            severity_multiplier = ss.severity / 10.0
            score = symptom_weight * severity_multiplier
            
            total_score += score
            total_weight += symptom_weight
        
        if total_weight == 0:
            return 1
        
        normalized_score = (total_score / total_weight) * 5
        return min(max(int(normalized_score), 1), 5)
    
    def _find_differential_diagnoses(self, session_symptoms) -> List[Dict[str, Any]]:
        """
        پیدا کردن تشخیص‌های افتراقی
        """
        symptom_ids = [ss.symptom.id for ss in session_symptoms]
        
        # پیدا کردن تشخیص‌هایی که علائم مطابق دارند
        diagnoses = DifferentialDiagnosis.objects.filter(
            typical_symptoms__id__in=symptom_ids,
            is_active=True
        ).distinct().annotate(
            matching_symptoms=Count('typical_symptoms', filter=Q(typical_symptoms__id__in=symptom_ids))
        ).order_by('-matching_symptoms', '-urgency_level')
        
        results = []
        for diagnosis in diagnoses[:10]:  # تا 10 تشخیص اول
            # محاسبه امتیاز احتمال
            probability = self._calculate_diagnosis_probability(diagnosis, session_symptoms)
            
            if probability > 0.1:  # حداقل 10% احتمال
                results.append({
                    'diagnosis': diagnosis,
                    'probability_score': probability,
                    'matching_symptoms_count': diagnosis.matching_symptoms,
                    'confidence_level': self._calculate_diagnosis_confidence(diagnosis, session_symptoms)
                })
        
        return sorted(results, key=lambda x: x['probability_score'], reverse=True)
    
    def _calculate_diagnosis_probability(self, diagnosis: DifferentialDiagnosis, session_symptoms) -> float:
        """
        محاسبه احتمال تشخیص
        """
        total_weight = 0
        matched_weight = 0
        
        # وزن کل علائم تشخیص
        diagnosis_symptoms = DiagnosisSymptom.objects.filter(diagnosis=diagnosis)
        for ds in diagnosis_symptoms:
            total_weight += ds.weight
            
            # بررسی وجود علامت در جلسه
            session_symptom = session_symptoms.filter(symptom=ds.symptom).first()
            if session_symptom:
                # وزن بر اساس شدت
                severity_factor = session_symptom.severity / 10.0
                matched_weight += ds.weight * severity_factor
        
        if total_weight == 0:
            return 0.0
        
        return min(matched_weight / total_weight, 1.0)
    
    def _calculate_diagnosis_confidence(self, diagnosis: DifferentialDiagnosis, session_symptoms) -> int:
        """
        محاسبه سطح اطمینان تشخیص
        """
        mandatory_symptoms = DiagnosisSymptom.objects.filter(
            diagnosis=diagnosis,
            is_mandatory=True
        )
        
        mandatory_present = 0
        for ms in mandatory_symptoms:
            if session_symptoms.filter(symptom=ms.symptom).exists():
                mandatory_present += 1
        
        if mandatory_symptoms.count() == 0:
            return 3  # اطمینان متوسط
        
        mandatory_ratio = mandatory_present / mandatory_symptoms.count()
        
        if mandatory_ratio >= 0.8:
            return 5  # اطمینان بالا
        elif mandatory_ratio >= 0.6:
            return 4
        elif mandatory_ratio >= 0.4:
            return 3
        elif mandatory_ratio >= 0.2:
            return 2
        else:
            return 1  # اطمینان کم
    
    def _apply_triage_rules(self, session: TriageSession, session_symptoms) -> List[Dict[str, Any]]:
        """
        اعمال قوانین تریاژ
        """
        applied_rules = []
        rules = TriageRule.objects.filter(is_active=True).order_by('-priority')
        
        for rule in rules:
            try:
                if self._evaluate_rule_conditions(rule, session, session_symptoms):
                    self._execute_rule_actions(rule, session)
                    applied_rules.append({
                        'rule_name': rule.name,
                        'actions': rule.actions,
                        'priority': rule.priority
                    })
            except Exception as e:
                logger.error(f"خطا در اعمال قانون {rule.name}: {e}")
        
        return applied_rules
    
    def _evaluate_rule_conditions(self, rule: TriageRule, session: TriageSession, session_symptoms) -> bool:
        """
        ارزیابی شرایط قانون
        """
        conditions = rule.conditions
        
        # شرایط علائم
        if 'required_symptoms' in conditions:
            required = conditions['required_symptoms']
            present_symptoms = [ss.symptom.name for ss in session_symptoms]
            if not all(symptom in present_symptoms for symptom in required):
                return False
        
        # شرایط اورژانس
        if 'min_urgency' in conditions:
            if session.urgency_level < conditions['min_urgency']:
                return False
        
        # شرایط شدت
        if 'min_severity' in conditions:
            max_severity = max([ss.severity for ss in session_symptoms], default=0)
            if max_severity < conditions['min_severity']:
                return False
        
        return True
    
    def _execute_rule_actions(self, rule: TriageRule, session: TriageSession):
        """
        اجرای اقدامات قانون
        """
        actions = rule.actions
        
        # تغییر سطح اورژانس
        if 'set_urgency' in actions:
            session.urgency_level = actions['set_urgency']
        
        # علامت‌گذاری برای توجه فوری
        if 'require_immediate_attention' in actions:
            session.requires_immediate_attention = actions['require_immediate_attention']
        
        # افزودن اقدامات توصیه شده
        if 'add_recommendations' in actions:
            new_recommendations = actions['add_recommendations']
            session.recommended_actions.extend(new_recommendations)
        
        session.save()
    
    def _detect_session_red_flags(self, session_symptoms) -> List[str]:
        """
        شناسایی علائم خطر در علائم جلسه
        """
        red_flags = []
        
        for ss in session_symptoms:
            # علائم با امتیاز اورژانس بالا
            if ss.symptom.urgency_score >= 8:
                red_flags.append(f"علامت اورژانسی: {ss.symptom.name}")
            
            # علائم با شدت بالا
            if ss.severity >= 8:
                red_flags.append(f"شدت بالای علامت: {ss.symptom.name}")
        
        return red_flags
    
    def _calculate_confidence_score(self, session_symptoms, possible_diagnoses: List[Dict]) -> float:
        """
        محاسبه امتیاز اطمینان کلی
        """
        if not session_symptoms.exists() or not possible_diagnoses:
            return 0.3
        
        # امتیاز بر اساس تعداد علائم
        symptom_score = min(session_symptoms.count() / 5.0, 1.0) * 0.3
        
        # امتیاز بر اساس بهترین تشخیص
        best_diagnosis_score = possible_diagnoses[0]['probability_score'] * 0.5 if possible_diagnoses else 0.0
        
        # امتیاز بر اساس تنوع تشخیص‌ها
        diagnosis_diversity = min(len(possible_diagnoses) / 3.0, 1.0) * 0.2
        
        return min(symptom_score + best_diagnosis_score + diagnosis_diversity, 1.0)
    
    def _save_session_diagnoses(self, session: TriageSession, possible_diagnoses: List[Dict]):
        """
        ذخیره تشخیص‌های احتمالی جلسه
        """
        # حذف تشخیص‌های قبلی
        SessionDiagnosis.objects.filter(session=session).delete()
        
        # ذخیره تشخیص‌های جدید
        for diag_data in possible_diagnoses:
            SessionDiagnosis.objects.create(
                session=session,
                diagnosis=diag_data['diagnosis'],
                probability_score=diag_data['probability_score'],
                confidence_level=diag_data['confidence_level'],
                reasoning=f"بر اساس {diag_data['matching_symptoms_count']} علامت مطابق"
            )
    
    def _match_symptoms_to_database(self, symptoms: List[str]) -> List[Symptom]:
        """
        تطبیق علائم با دیتابیس
        """
        matched_symptoms = []
        
        for symptom_text in symptoms:
            # جستجوی دقیق
            exact_match = Symptom.objects.filter(
                Q(name__iexact=symptom_text) | Q(name_en__iexact=symptom_text),
                is_active=True
            ).first()
            
            if exact_match:
                matched_symptoms.append(exact_match)
                continue
            
            # جستجوی تقریبی
            fuzzy_matches = Symptom.objects.filter(
                Q(name__icontains=symptom_text) | Q(name_en__icontains=symptom_text),
                is_active=True
            )[:3]  # حداکثر 3 تطبیق
            
            matched_symptoms.extend(fuzzy_matches)
        
        return list(set(matched_symptoms))  # حذف تکراری‌ها
    
    def _calculate_standalone_urgency(self, symptoms: List[Symptom], severity_scores: Dict[str, int]) -> int:
        """
        محاسبه اورژانس برای تحلیل مستقل
        """
        if not symptoms:
            return 1
        
        total_score = 0
        total_weight = 0
        
        for symptom in symptoms:
            urgency_weight = self.urgency_weights.get(symptom.urgency_score, 0.1)
            severity = severity_scores.get(symptom.name, 5)  # شدت پیش‌فرض 5
            severity_multiplier = severity / 10.0
            
            score = urgency_weight * severity_multiplier
            total_score += score
            total_weight += urgency_weight
        
        if total_weight == 0:
            return 1
        
        normalized_score = (total_score / total_weight) * 5
        return min(max(int(normalized_score), 1), 5)
    
    def _generate_recommendations(self, session: TriageSession, possible_diagnoses: List[Dict]) -> List[str]:
        """
        تولید توصیه‌های کلی
        """
        recommendations = []
        
        if session.urgency_level >= 4:
            recommendations.append("مراجعه فوری به پزشک یا اورژانس")
        elif session.urgency_level == 3:
            recommendations.append("مراجعه به پزشک در اسرع وقت")
        elif session.urgency_level == 2:
            recommendations.append("مراجعه به پزشک در روزهای آینده")
        else:
            recommendations.append("مراقبت خانگی و نظارت بر علائم")
        
        # توصیه‌های بر اساس تشخیص‌ها
        for diag_data in possible_diagnoses[:3]:
            diagnosis = diag_data['diagnosis']
            if diagnosis.recommended_actions:
                recommendations.extend(diagnosis.recommended_actions)
        
        return list(set(recommendations))  # حذف تکراری‌ها
    
    def _get_initial_recommendations(self, urgency: int, red_flags: List[str]) -> List[str]:
        """
        توصیه‌های اولیه
        """
        recommendations = []
        
        if red_flags:
            recommendations.append("فوراً به اورژانس مراجعه کنید")
        elif urgency >= 4:
            recommendations.append("در اسرع وقت به پزشک مراجعه کنید")
        else:
            recommendations.append("علائم خود را دقیق‌تر بررسی کنید")
        
        return recommendations