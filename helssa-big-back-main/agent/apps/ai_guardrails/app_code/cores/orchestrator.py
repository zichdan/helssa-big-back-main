# ruff: noqa: RUF002, RUF003
"""
هماهنگ‌کننده مرکزی برای اپلیکیشن
Central Orchestrator for Application
"""

from app_standards.four_cores import CentralOrchestrator
from typing import Dict, Any, List
import uuid
from django.db.models import Q
from ..models import GuardrailPolicy, RedFlagRule, PolicyViolationLog
import re


class GuardrailsOrchestrator(CentralOrchestrator):
    """
    هماهنگ‌کننده ارزیابی گاردریل بر اساس سیاست‌ها و قوانین رد-فلگ
    """

    def evaluate(self, content: str, user, direction: str = 'both', request=None) -> Dict[str, Any]:
        """
        ارزیابی محتوای ورودی/خروجی و بازگرداندن نتیجه تصمیم‌گیری
        """
        active_policies = GuardrailPolicy.objects.filter(is_active=True).order_by('priority')
        direction = direction if direction in {"input", "output", "both"} else "both"
        if direction in ['input', 'output']:
            active_policies = active_policies.filter(Q(applies_to=direction) | Q(applies_to='both'))
        matches: list[dict[str, Any]] = []
        reasons: list[str] = []
        max_severity = 0
        first_matched_rule = None  # RedFlagRule | None

        rules = RedFlagRule.objects.filter(is_active=True)
        for rule in rules:
            if rule.pattern_type == 'keyword':
                if rule.pattern in content:
                    span_positions = [(m.start(), m.end()) for m in re.finditer(re.escape(rule.pattern), content)]
                    matches.append({
                        'rule': rule.name,
                        'category': rule.category,
                        'severity': rule.severity,
                        'spans': span_positions
                    })
                    reasons.append(f"matched:{rule.category}:{rule.name}")
                    max_severity = max(max_severity, rule.severity)
            else:
                try:
                    reg = re.compile(rule.pattern, re.IGNORECASE)
                    span_positions = [(m.start(), m.end()) for m in reg.finditer(content)]
                    if span_positions:
                        matches.append({
                            'rule': rule.name,
                            'category': rule.category,
                            'severity': rule.severity,
                            'spans': span_positions
                        })
                        reasons.append(f"matched:{rule.category}:{rule.name}")
                        max_severity = max(max_severity, rule.severity)
                except re.error:
                    # الگوی نامعتبر را نادیده بگیر
                    continue

        # تصمیم بر اساس سیاست‌ها (اولین سیاست با اولویت بالاتر اعمال می‌شود)
        action = 'allow'
        applied_policy = None
        for policy in active_policies:
            threshold = int(policy.conditions.get('severity_min', 0)) if isinstance(policy.conditions, dict) else 0
            if max_severity >= threshold and matches:
                if policy.enforcement_mode == 'block':
                    action = 'block'
                elif policy.enforcement_mode == 'warn':
                    action = 'warn'
                else:
                    action = 'allow'
                applied_policy = policy
                break

        allowed = action == 'allow'
        risk_score = max_severity

        # ثبت لاگ نقض سیاست در صورت نیاز
        if action in ['block', 'warn'] and matches:
            first_matched_rule_name = matches[0]['rule']
            matched_rule = next((r for r in rules if r.name == first_matched_rule_name), None)
            # ماسک کردن بخش‌های حساس قبل از لاگ: کاراکترهای منطبق را با * جایگزین می‌کنیم
            masked_snapshot = content[:1000]
            for m in matches:
                for start, end in m.get('spans', []):
                    if 0 <= start < end <= len(masked_snapshot):
                        masked_snapshot = masked_snapshot[:start] + ('*' * (end - start)) + masked_snapshot[end:]

            # استخراج IP واقعی با درنظر گرفتن X-Forwarded-For
            client_ip = ''
            if request:
                xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
                client_ip = (xff.split(',')[0].strip() if xff else '') or request.META.get('REMOTE_ADDR', '')

            PolicyViolationLog.objects.create(
                user=user if getattr(user, 'is_authenticated', False) else None,
                policy=applied_policy,
                rule=matched_rule,
                content_snapshot=masked_snapshot,
                direction=direction if direction in ['input', 'output'] else 'input',
                context={'reasons': reasons},
                action_taken='blocked' if action == 'block' else 'warned',
                risk_score=risk_score,
                matched_spans=matches,
                request_path=(request.path if request and hasattr(request, 'path') else ''),
                ip_address=client_ip,
                user_agent=(request.META.get('HTTP_USER_AGENT', '') if request else '')
            )

        return {
            'allowed': allowed,
            'action': action,
            'risk_score': risk_score,
            'reasons': reasons,
            'matches': matches,
            'applied_policy': applied_policy.name if applied_policy else '',
            'applied_policy_id': str(applied_policy.id) if applied_policy else None,
            'decision_id': str(uuid.uuid4()),
        }


# پیاده‌سازی خاص اپلیکیشن را اینجا اضافه کنید
