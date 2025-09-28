"""
مقداردهی اولیه داده‌های Privacy
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from ...models import DataClassification, DataField, DataRetentionPolicy


class Command(BaseCommand):
    """
    دستور مقداردهی اولیه داده‌های Privacy
    """
    help = 'مقداردهی اولیه طبقه‌بندی‌ها، فیلدها و سیاست‌های حریم خصوصی'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='حذف داده‌های موجود و ایجاد مجدد',
        )

    def handle(self, *args, **options):
        """اجرای دستور"""
        
        if options['force']:
            self.stdout.write('حذف داده‌های موجود...')
            DataField.objects.all().delete()
            DataRetentionPolicy.objects.all().delete()
            DataClassification.objects.all().delete()

        with transaction.atomic():
            # ایجاد طبقه‌بندی‌های پایه
            self.create_classifications()
            
            # ایجاد فیلدهای داده
            self.create_data_fields()
            
            # ایجاد سیاست‌های نگهداری
            self.create_retention_policies()

        self.stdout.write(
            self.style.SUCCESS('مقداردهی اولیه با موفقیت انجام شد')
        )

    def create_classifications(self):
        """ایجاد طبقه‌بندی‌های پایه"""
        self.stdout.write('ایجاد طبقه‌بندی‌های داده...')
        
        classifications = [
            {
                'name': 'اطلاعات عمومی',
                'classification_type': 'public',
                'description': 'اطلاعات قابل دسترس برای عموم',
                'retention_period_days': 365
            },
            {
                'name': 'اطلاعات داخلی',
                'classification_type': 'internal',
                'description': 'اطلاعات داخلی سازمان',
                'retention_period_days': 1095  # 3 سال
            },
            {
                'name': 'اطلاعات محرمانه',
                'classification_type': 'confidential',
                'description': 'اطلاعات محرمانه سازمان',
                'retention_period_days': 2555  # 7 سال
            },
            {
                'name': 'اطلاعات محدود',
                'classification_type': 'restricted',
                'description': 'اطلاعات با دسترسی بسیار محدود',
                'retention_period_days': 3650  # 10 سال
            },
            {
                'name': 'اطلاعات شخصی قابل شناسایی',
                'classification_type': 'pii',
                'description': 'اطلاعات شخصی که می‌تواند فرد را شناسایی کند',
                'retention_period_days': 1095  # 3 سال
            },
            {
                'name': 'اطلاعات سلامت محافظت‌شده',
                'classification_type': 'phi',
                'description': 'اطلاعات پزشکی و سلامت بیماران',
                'retention_period_days': 3650  # 10 سال
            }
        ]
        
        for cls_data in classifications:
            classification, created = DataClassification.objects.get_or_create(
                classification_type=cls_data['classification_type'],
                defaults=cls_data
            )
            
            if created:
                self.stdout.write(f'  ✓ {classification.name}')
            else:
                self.stdout.write(f'  - {classification.name} (موجود)')

    def create_data_fields(self):
        """ایجاد فیلدهای داده نمونه"""
        self.stdout.write('ایجاد فیلدهای داده...')
        
        # دریافت طبقه‌بندی‌ها
        pii_class = DataClassification.objects.get(classification_type='pii')
        phi_class = DataClassification.objects.get(classification_type='phi')
        confidential_class = DataClassification.objects.get(classification_type='confidential')
        
        fields = [
            # فیلدهای PII
            {
                'field_name': 'national_code',
                'model_name': 'UserProfile',
                'app_name': 'auth_otp',
                'classification': pii_class,
                'redaction_pattern': r'\b\d{10}\b',
                'replacement_text': '[کد ملی حذف شده]'
            },
            {
                'field_name': 'phone_number',
                'model_name': 'UserProfile', 
                'app_name': 'auth_otp',
                'classification': pii_class,
                'redaction_pattern': r'\b09\d{9}\b',
                'replacement_text': '[شماره تلفن حذف شده]'
            },
            {
                'field_name': 'email',
                'model_name': 'UserProfile',
                'app_name': 'auth_otp',
                'classification': pii_class,
                'redaction_pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'replacement_text': '[ایمیل حذف شده]'
            },
            {
                'field_name': 'address',
                'model_name': 'PatientProfile',
                'app_name': 'patient',
                'classification': pii_class,
                'redaction_pattern': r'آدرس\s+[^\s]+',
                'replacement_text': '[آدرس حذف شده]'
            },
            
            # فیلدهای PHI
            {
                'field_name': 'medical_record_number',
                'model_name': 'PatientProfile',
                'app_name': 'patient',
                'classification': phi_class,
                'redaction_pattern': r'\bMR\d{6,10}\b',
                'replacement_text': '[شماره پرونده حذف شده]'
            },
            {
                'field_name': 'diagnosis',
                'model_name': 'MedicalRecord',
                'app_name': 'encounters',
                'classification': phi_class,
                'redaction_pattern': r'تشخیص:\s*[^\n]+',
                'replacement_text': '[تشخیص حذف شده]'
            },
            {
                'field_name': 'prescription',
                'model_name': 'MedicalRecord',
                'app_name': 'encounters',
                'classification': phi_class,
                'redaction_pattern': r'نسخه:\s*[^\n]+',
                'replacement_text': '[نسخه حذف شده]'
            },
            {
                'field_name': 'lab_results',
                'model_name': 'LabTest',
                'app_name': 'encounters',
                'classification': phi_class,
                'redaction_pattern': r'آزمایش:\s*[^\n]+',
                'replacement_text': '[نتایج آزمایش حذف شده]'
            },
            
            # فیلدهای محرمانه
            {
                'field_name': 'payment_info',
                'model_name': 'Payment',
                'app_name': 'payments',
                'classification': confidential_class,
                'redaction_pattern': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
                'replacement_text': '[اطلاعات پرداخت حذف شده]'
            }
        ]
        
        for field_data in fields:
            field, created = DataField.objects.get_or_create(
                field_name=field_data['field_name'],
                model_name=field_data['model_name'],
                app_name=field_data['app_name'],
                defaults=field_data
            )
            
            if created:
                self.stdout.write(f'  ✓ {field}')
            else:
                self.stdout.write(f'  - {field} (موجود)')

    def create_retention_policies(self):
        """ایجاد سیاست‌های نگهداری"""
        self.stdout.write('ایجاد سیاست‌های نگهداری...')
        
        classifications = DataClassification.objects.all()
        
        policies = [
            {
                'name': 'سیاست نگهداری اطلاعات شخصی',
                'classification': DataClassification.objects.get(classification_type='pii'),
                'retention_period_days': 1095,  # 3 سال
                'auto_delete': False,
                'archive_before_delete': True,
                'notification_days_before': 30,
                'description': 'اطلاعات شخصی باید حداکثر 3 سال نگهداری شود'
            },
            {
                'name': 'سیاست نگهداری اطلاعات پزشکی',
                'classification': DataClassification.objects.get(classification_type='phi'),
                'retention_period_days': 3650,  # 10 سال
                'auto_delete': False,
                'archive_before_delete': True,
                'notification_days_before': 60,
                'description': 'اطلاعات پزشکی باید حداکثر 10 سال نگهداری شود'
            },
            {
                'name': 'سیاست نگهداری اطلاعات محرمانه',
                'classification': DataClassification.objects.get(classification_type='confidential'),
                'retention_period_days': 2555,  # 7 سال
                'auto_delete': False,
                'archive_before_delete': True,
                'notification_days_before': 45,
                'description': 'اطلاعات محرمانه باید حداکثر 7 سال نگهداری شود'
            }
        ]
        
        for policy_data in policies:
            policy, created = DataRetentionPolicy.objects.get_or_create(
                name=policy_data['name'],
                defaults=policy_data
            )
            
            if created:
                self.stdout.write(f'  ✓ {policy.name}')
            else:
                self.stdout.write(f'  - {policy.name} (موجود)')

        self.stdout.write(
            self.style.SUCCESS(f'مقداردهی کامل شد:\n'
                             f'  - {DataClassification.objects.count()} طبقه‌بندی\n'
                             f'  - {DataField.objects.count()} فیلد داده\n'
                             f'  - {DataRetentionPolicy.objects.count()} سیاست نگهداری')
        )