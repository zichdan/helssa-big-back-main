from __future__ import annotations

"""
سرویس‌های اپ SOAP برای تولید گزارش و خروجی‌ها
"""

from typing import Dict, Any
from datetime import datetime


class SOAPReportGenerator:
    """
    تولیدکننده گزارش SOAP از متن رونویسی
    """

    def generate(self, transcript: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        تولید بخش‌های SOAP بر اساس مستندات نمونه

        Args:
            transcript: متن رونویسی
            context: اطلاعات بیمار و پزشک

        Returns:
            dict: ساختار گزارش SOAP
        """
        # ساختار پایه مطابق مستندات نمونه
        subjective = {
            'chief_complaint': '',
            'hpi': {'narrative': ''},
            'pmh': [],
            'medications': [],
            'allergies': []
        }
        objective = {
            'vital_signs': {},
            'physical_exam': ''
        }
        assessment = {
            'diagnoses': []
        }
        plan = {
            'medications': [],
            'lab_orders': [],
            'follow_up': ''
        }

        soap_report = {
            'encounter_id': context.get('encounter_id', ''),
            'generated_at': datetime.now().isoformat(),
            'subjective': subjective,
            'objective': objective,
            'assessment': assessment,
            'plan': plan,
            'metadata': {
                'generator_version': '1.0',
                'word_count': len(transcript.split()) if transcript else 0
            }
        }

        return soap_report


def generate_markdown(soap_report: Dict[str, Any]) -> str:
    """
    تولید خروجی Markdown بر اساس نمونه مستندات
    """
    md = (
        f"# گزارش SOAP\n\n"
        f"تاریخ: {soap_report['generated_at']}\n"
        f"شماره ملاقات: {soap_report['encounter_id']}\n\n"
        f"## Subjective (شرح حال)\n\n"
        f"**شکایت اصلی:** {soap_report['subjective'].get('chief_complaint', '')}\n\n"
        f"**تاریخچه بیماری فعلی:**\n"
        f"{soap_report['subjective'].get('hpi', {}).get('narrative', '')}\n\n"
        f"## Objective (معاینه)\n\n"
        f"**علائم حیاتی:**\n"
        f"- فشار خون: {soap_report['objective'].get('vital_signs', {}).get('bp', 'ثبت نشده')}\n"
        f"- ضربان قلب: {soap_report['objective'].get('vital_signs', {}).get('hr', 'ثبت نشده')}\n"
        f"- تنفس: {soap_report['objective'].get('vital_signs', {}).get('rr', 'ثبت نشده')}\n"
        f"- دما: {soap_report['objective'].get('vital_signs', {}).get('temp', 'ثبت نشده')}\n\n"
        f"**معاینه فیزیکی:**\n"
        f"{soap_report['objective'].get('physical_exam', 'انجام نشده')}\n\n"
        f"## Assessment (ارزیابی)\n\n"
        f"## Plan (برنامه درمان)\n\n"
    )
    return md