"""
هسته پردازش متن سیستم مالی
Financial System Text Processing Core
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import json


class BillingTextProcessorCore:
    """
    هسته پردازش متن برای سیستم مالی
    مسئول تحلیل و پردازش متون مربوط به تراکنش‌ها، فاکتورها و گزارش‌های مالی
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._initialize_patterns()
        
    def _initialize_patterns(self):
        """مقداردهی اولیه الگوهای regex"""
        self.patterns = {
            # الگوهای مبلغ
            'amount_rial': r'(\d{1,3}(?:,\d{3})*)\s*ریال',
            'amount_toman': r'(\d{1,3}(?:,\d{3})*)\s*تومان',
            'amount_number': r'(\d{1,3}(?:,\d{3})*)',
            
            # الگوهای شماره کارت
            'card_number': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'card_partial': r'\*+\d{4}',
            
            # الگوهای تاریخ
            'date_persian': r'(\d{4})/(\d{1,2})/(\d{1,2})',
            'date_gregorian': r'(\d{1,2})/(\d{1,2})/(\d{4})',
            
            # الگوهای شماره تراکنش
            'transaction_ref': r'[A-Z]{2,4}\d{8,20}',
            'invoice_number': r'INV\d{8,12}',
            
            # الگوهای شماره موبایل
            'mobile_number': r'09\d{9}',
        }
        
        # کلمات کلیدی مالی
        self.financial_keywords = {
            'payment': ['پرداخت', 'واریز', 'پرداختی', 'تسویه'],
            'withdrawal': ['برداشت', 'خروج', 'انتقال'],
            'refund': ['بازگشت', 'استرداد', 'برگشت'],
            'commission': ['کمیسیون', 'کارمزد', 'هزینه'],
            'subscription': ['اشتراک', 'عضویت', 'پلن'],
            'invoice': ['فاکتور', 'صورتحساب', 'قبض'],
            'balance': ['موجودی', 'اعتبار', 'مانده'],
        }
        
    def extract_financial_entities(self, text: str) -> Dict[str, Any]:
        """
        استخراج موجودیت‌های مالی از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            Dict: موجودیت‌های استخراج شده
        """
        try:
            entities = {
                'amounts': [],
                'card_numbers': [],
                'dates': [],
                'transaction_refs': [],
                'mobile_numbers': [],
                'keywords': [],
            }
            
            # استخراج مبالغ
            entities['amounts'] = self._extract_amounts(text)
            
            # استخراج شماره کارت‌ها
            entities['card_numbers'] = self._extract_card_numbers(text)
            
            # استخراج تاریخ‌ها
            entities['dates'] = self._extract_dates(text)
            
            # استخراج شماره تراکنش‌ها
            entities['transaction_refs'] = self._extract_transaction_refs(text)
            
            # استخراج شماره موبایل‌ها
            entities['mobile_numbers'] = self._extract_mobile_numbers(text)
            
            # استخراج کلمات کلیدی
            entities['keywords'] = self._extract_keywords(text)
            
            return entities
            
        except Exception as e:
            self.logger.error(f"خطا در استخراج موجودیت‌های مالی: {str(e)}")
            return {}
    
    def _extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        """استخراج مبالغ از متن"""
        amounts = []
        
        # مبالغ ریالی
        rial_matches = re.finditer(self.patterns['amount_rial'], text, re.IGNORECASE)
        for match in rial_matches:
            amount_str = match.group(1).replace(',', '')
            amounts.append({
                'value': int(amount_str),
                'currency': 'rial',
                'text': match.group(0),
                'position': match.span()
            })
        
        # مبالغ تومانی
        toman_matches = re.finditer(self.patterns['amount_toman'], text, re.IGNORECASE)
        for match in toman_matches:
            amount_str = match.group(1).replace(',', '')
            amounts.append({
                'value': int(amount_str) * 10,  # تبدیل به ریال
                'currency': 'toman',
                'text': match.group(0),
                'position': match.span()
            })
        
        return amounts
    
    def _extract_card_numbers(self, text: str) -> List[Dict[str, Any]]:
        """استخراج شماره کارت‌ها از متن"""
        cards = []
        
        # شماره کارت کامل
        card_matches = re.finditer(self.patterns['card_number'], text)
        for match in card_matches:
            card_number = re.sub(r'[\s-]', '', match.group(0))
            cards.append({
                'number': card_number,
                'masked': self._mask_card_number(card_number),
                'text': match.group(0),
                'position': match.span()
            })
        
        # شماره کارت ماسک شده
        partial_matches = re.finditer(self.patterns['card_partial'], text)
        for match in partial_matches:
            cards.append({
                'number': None,
                'masked': match.group(0),
                'text': match.group(0),
                'position': match.span()
            })
        
        return cards
    
    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """استخراج تاریخ‌ها از متن"""
        dates = []
        
        # تاریخ شمسی
        persian_matches = re.finditer(self.patterns['date_persian'], text)
        for match in persian_matches:
            dates.append({
                'year': int(match.group(1)),
                'month': int(match.group(2)),
                'day': int(match.group(3)),
                'type': 'persian',
                'text': match.group(0),
                'position': match.span()
            })
        
        return dates
    
    def _extract_transaction_refs(self, text: str) -> List[Dict[str, Any]]:
        """استخراج شماره مرجع تراکنش‌ها"""
        refs = []
        
        # شماره مرجع عمومی
        ref_matches = re.finditer(self.patterns['transaction_ref'], text)
        for match in ref_matches:
            refs.append({
                'reference': match.group(0),
                'type': 'transaction',
                'text': match.group(0),
                'position': match.span()
            })
        
        # شماره فاکتور
        invoice_matches = re.finditer(self.patterns['invoice_number'], text)
        for match in invoice_matches:
            refs.append({
                'reference': match.group(0),
                'type': 'invoice',
                'text': match.group(0),
                'position': match.span()
            })
        
        return refs
    
    def _extract_mobile_numbers(self, text: str) -> List[Dict[str, Any]]:
        """استخراج شماره موبایل‌ها"""
        mobiles = []
        
        mobile_matches = re.finditer(self.patterns['mobile_number'], text)
        for match in mobile_matches:
            mobiles.append({
                'number': match.group(0),
                'masked': f"{match.group(0)[:4]}***{match.group(0)[-3:]}",
                'text': match.group(0),
                'position': match.span()
            })
        
        return mobiles
    
    def _extract_keywords(self, text: str) -> List[Dict[str, Any]]:
        """استخراج کلمات کلیدی مالی"""
        keywords = []
        
        for category, words in self.financial_keywords.items():
            for word in words:
                if word in text:
                    keywords.append({
                        'word': word,
                        'category': category,
                        'confidence': 1.0
                    })
        
        return keywords
    
    def _mask_card_number(self, card_number: str) -> str:
        """ماسک کردن شماره کارت"""
        if len(card_number) >= 4:
            return f"****-****-****-{card_number[-4:]}"
        return "****"
    
    def analyze_transaction_description(self, description: str) -> Dict[str, Any]:
        """
        تحلیل توضیحات تراکنش
        
        Args:
            description: توضیحات تراکنش
            
        Returns:
            Dict: نتایج تحلیل
        """
        try:
            # استخراج موجودیت‌ها
            entities = self.extract_financial_entities(description)
            
            # تشخیص نوع تراکنش
            transaction_type = self._detect_transaction_type(description, entities)
            
            # استخراج اطلاعات مقصد/مبدأ
            party_info = self._extract_party_info(description, entities)
            
            # محاسبه امتیاز اعتماد
            confidence_score = self._calculate_confidence(entities)
            
            return {
                'entities': entities,
                'transaction_type': transaction_type,
                'party_info': party_info,
                'confidence_score': confidence_score,
                'summary': self._generate_summary(description, entities)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل توضیحات تراکنش: {str(e)}")
            return {}
    
    def _detect_transaction_type(self, text: str, entities: Dict[str, Any]) -> str:
        """تشخیص نوع تراکنش از متن"""
        keywords = entities.get('keywords', [])
        
        # اولویت‌بندی بر اساس کلمات کلیدی
        type_scores = {}
        for keyword in keywords:
            category = keyword['category']
            confidence = keyword['confidence']
            type_scores[category] = type_scores.get(category, 0) + confidence
        
        if type_scores:
            return max(type_scores, key=type_scores.get)
        
        return 'unknown'
    
    def _extract_party_info(self, text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج اطلاعات طرف مقابل تراکنش"""
        party_info = {}
        
        # شماره موبایل
        mobile_numbers = entities.get('mobile_numbers', [])
        if mobile_numbers:
            party_info['mobile'] = mobile_numbers[0]['number']
        
        # شماره کارت
        card_numbers = entities.get('card_numbers', [])
        if card_numbers:
            party_info['card'] = card_numbers[0]['masked']
        
        return party_info
    
    def _calculate_confidence(self, entities: Dict[str, Any]) -> float:
        """محاسبه امتیاز اعتماد برای تحلیل"""
        score = 0.0
        
        # موجودیت‌های یافت شده
        if entities.get('amounts'):
            score += 0.3
        if entities.get('keywords'):
            score += 0.2
        if entities.get('transaction_refs'):
            score += 0.2
        if entities.get('dates'):
            score += 0.1
        if entities.get('mobile_numbers') or entities.get('card_numbers'):
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_summary(self, text: str, entities: Dict[str, Any]) -> str:
        """تولید خلاصه از تحلیل"""
        summary_parts = []
        
        # مبلغ
        amounts = entities.get('amounts', [])
        if amounts:
            amount = amounts[0]
            summary_parts.append(f"مبلغ: {amount['value']:,} ریال")
        
        # نوع تراکنش
        keywords = entities.get('keywords', [])
        if keywords:
            keyword = keywords[0]
            summary_parts.append(f"نوع: {keyword['word']}")
        
        # شماره مرجع
        refs = entities.get('transaction_refs', [])
        if refs:
            ref = refs[0]
            summary_parts.append(f"مرجع: {ref['reference']}")
        
        return " | ".join(summary_parts) if summary_parts else "اطلاعات کافی یافت نشد"
    
    def generate_financial_report_text(self, data: Dict[str, Any], report_type: str) -> str:
        """
        تولید متن گزارش مالی
        
        Args:
            data: داده‌های گزارش
            report_type: نوع گزارش (wallet, transaction, subscription)
            
        Returns:
            str: متن گزارش فرمت شده
        """
        try:
            if report_type == 'wallet':
                return self._generate_wallet_report(data)
            elif report_type == 'transaction':
                return self._generate_transaction_report(data)
            elif report_type == 'subscription':
                return self._generate_subscription_report(data)
            else:
                return "نوع گزارش نامشخص"
                
        except Exception as e:
            self.logger.error(f"خطا در تولید گزارش: {str(e)}")
            return "خطا در تولید گزارش"
    
    def _generate_wallet_report(self, data: Dict[str, Any]) -> str:
        """تولید گزارش کیف پول"""
        balance = data.get('balance', 0)
        blocked = data.get('blocked_balance', 0)
        available = balance - blocked
        
        report = f"""
📊 گزارش کیف پول

💰 موجودی کل: {balance:,} ریال
🔒 موجودی بلوکه شده: {blocked:,} ریال
✅ موجودی قابل استفاده: {available:,} ریال

📈 وضعیت: {"تأیید شده" if data.get('is_verified') else "تأیید نشده"}
        """
        
        return report.strip()
    
    def _generate_transaction_report(self, data: Dict[str, Any]) -> str:
        """تولید گزارش تراکنش"""
        amount = data.get('amount', 0)
        type_display = data.get('type_display', 'نامشخص')
        status_display = data.get('status_display', 'نامشخص')
        
        report = f"""
💳 گزارش تراکنش

🔢 مبلغ: {amount:,} ریال
📋 نوع: {type_display}
📊 وضعیت: {status_display}
🔗 شماره مرجع: {data.get('reference_number', 'نامشخص')}

📅 تاریخ: {data.get('created_at', 'نامشخص')}
        """
        
        return report.strip()
    
    def _generate_subscription_report(self, data: Dict[str, Any]) -> str:
        """تولید گزارش اشتراک"""
        plan_name = data.get('plan_name', 'نامشخص')
        status_display = data.get('status_display', 'نامشخص')
        
        report = f"""
📋 گزارش اشتراک

📦 پلن: {plan_name}
📊 وضعیت: {status_display}
💰 قیمت: {data.get('price', 0):,} ریال
📅 تاریخ شروع: {data.get('start_date', 'نامشخص')}
📅 تاریخ پایان: {data.get('end_date', 'نامشخص')}

🔄 تمدید خودکار: {"فعال" if data.get('auto_renew') else "غیرفعال"}
        """
        
        return report.strip()