from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


class FHIRTransformer:
    """
    کلاس برای تبدیل داده‌های داخلی به FHIR
    """
    
    def transform(
        self,
        source_model: str,
        source_id: str,
        mapping: 'FHIRMapping',
        include_related: bool = False
    ) -> Dict[str, Any]:
        """
        تبدیل یک رکورد به منبع FHIR
        
        Args:
            source_model: نام مدل منبع
            source_id: شناسه رکورد منبع
            mapping: شیء نقشه‌برداری
            include_related: شامل کردن داده‌های مرتبط
            
        Returns:
            dict: منبع FHIR تولید شده
        """
        try:
            # دریافت مدل و رکورد
            model_class = apps.get_model(source_model)
            instance = model_class.objects.get(pk=source_id)
            
            # ساخت منبع FHIR پایه
            fhir_resource = {
                'resourceType': mapping.target_resource_type,
                'id': str(source_id)
            }
            
            # اعمال نقشه‌برداری فیلدها
            for source_field, target_path in mapping.field_mappings.items():
                value = self._get_field_value(instance, source_field)
                
                if value is not None:
                    if isinstance(target_path, str):
                        # مسیر ساده
                        self._set_nested_value(fhir_resource, target_path, value)
                    elif isinstance(target_path, dict):
                        # نقشه‌برداری پیچیده
                        transformed_value = self._apply_transformation(
                            value,
                            target_path,
                            mapping.transformation_rules.get(source_field, {})
                        )
                        if 'path' in target_path:
                            self._set_nested_value(
                                fhir_resource,
                                target_path['path'],
                                transformed_value
                            )
            
            # اضافه کردن متادیتا
            fhir_resource['meta'] = {
                'lastUpdated': datetime.now().isoformat(),
                'source': f"{source_model}/{source_id}"
            }
            
            # پردازش داده‌های مرتبط
            if include_related:
                related_resources = self._get_related_resources(
                    instance,
                    mapping.transformation_rules.get('related', {})
                )
                if related_resources:
                    fhir_resource['contained'] = related_resources
            
            return {'resource': fhir_resource, 'success': True}
            
        except ObjectDoesNotExist:
            logger.error(f"رکورد {source_id} در مدل {source_model} یافت نشد")
            raise ValueError(f"رکورد یافت نشد: {source_model}/{source_id}")
        except Exception as e:
            logger.error(f"خطا در تبدیل: {str(e)}")
            raise
    
    def _get_field_value(self, instance: Any, field_path: str) -> Any:
        """
        دریافت مقدار فیلد از instance با پشتیبانی از مسیرهای تودرتو
        """
        parts = field_path.split('.')
        value = instance
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
                # اگر متد است، فراخوانی کن
                if callable(value):
                    value = value()
            else:
                return None
        
        return value
    
    def _set_nested_value(self, obj: Dict, path: str, value: Any) -> None:
        """
        تنظیم مقدار در مسیر تودرتو
        """
        parts = path.split('.')
        current = obj
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def _apply_transformation(
        self,
        value: Any,
        target_config: Dict[str, Any],
        transformation_rules: Dict[str, Any]
    ) -> Any:
        """
        اعمال قوانین تبدیل روی مقدار
        """
        # نوع داده هدف
        if 'type' in target_config:
            value = self._convert_type(value, target_config['type'])
        
        # فرمت
        if 'format' in target_config:
            value = self._format_value(value, target_config['format'])
        
        # mapping مقادیر
        if 'value_map' in transformation_rules:
            value_map = transformation_rules['value_map']
            if str(value) in value_map:
                value = value_map[str(value)]
        
        return value
    
    def _convert_type(self, value: Any, target_type: str) -> Any:
        """
        تبدیل نوع داده
        """
        if target_type == 'string':
            return str(value)
        elif target_type == 'integer':
            return int(value)
        elif target_type == 'boolean':
            return bool(value)
        elif target_type == 'date':
            if isinstance(value, datetime):
                return value.date().isoformat()
            return str(value)
        elif target_type == 'dateTime':
            if isinstance(value, datetime):
                return value.isoformat()
            return str(value)
        
        return value
    
    def _format_value(self, value: Any, format_spec: str) -> Any:
        """
        فرمت کردن مقدار
        """
        if format_spec == 'upper':
            return str(value).upper()
        elif format_spec == 'lower':
            return str(value).lower()
        elif format_spec == 'title':
            return str(value).title()
        
        return value
    
    def _get_related_resources(
        self,
        instance: Any,
        related_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        دریافت منابع مرتبط
        """
        related_resources = []
        
        for relation_name, config in related_config.items():
            if hasattr(instance, relation_name):
                related_objects = getattr(instance, relation_name)
                
                # اگر رابطه many-to-many یا reverse foreign key است
                if hasattr(related_objects, 'all'):
                    related_objects = related_objects.all()
                else:
                    related_objects = [related_objects] if related_objects else []
                
                for related_obj in related_objects:
                    # تبدیل شیء مرتبط به منبع FHIR
                    # این بخش نیاز به پیاده‌سازی بیشتر دارد
                    pass
        
        return related_resources


class FHIRValidator:
    """
    کلاس برای اعتبارسنجی منابع FHIR
    """
    
    def validate(
        self,
        resource_type: str,
        resource_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        اعتبارسنجی یک منبع FHIR
        
        Returns:
            dict: نتیجه اعتبارسنجی شامل valid, errors, warnings
        """
        errors = []
        warnings = []
        
        # بررسی فیلدهای الزامی پایه
        if 'resourceType' not in resource_content:
            errors.append("فیلد resourceType الزامی است")
        elif resource_content['resourceType'] != resource_type:
            errors.append(
                f"نوع منبع نامطابق: انتظار {resource_type}، "
                f"دریافت {resource_content['resourceType']}"
            )
        
        # اعتبارسنجی‌های خاص هر نوع منبع
        validator_method = getattr(
            self,
            f'_validate_{resource_type.lower()}',
            None
        )
        
        if validator_method:
            type_errors, type_warnings = validator_method(resource_content)
            errors.extend(type_errors)
            warnings.extend(type_warnings)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_patient(self, resource: Dict[str, Any]) -> tuple:
        """اعتبارسنجی منبع Patient"""
        errors = []
        warnings = []
        
        # حداقل یک identifier یا name باید وجود داشته باشد
        if 'identifier' not in resource and 'name' not in resource:
            errors.append("Patient باید حداقل یک identifier یا name داشته باشد")
        
        # بررسی ساختار name
        if 'name' in resource:
            for name in resource['name']:
                if not isinstance(name, dict):
                    errors.append("name باید یک شیء باشد")
                elif 'family' not in name and 'given' not in name:
                    warnings.append("name باید family یا given داشته باشد")
        
        return errors, warnings
    
    def _validate_encounter(self, resource: Dict[str, Any]) -> tuple:
        """اعتبارسنجی منبع Encounter"""
        errors = []
        warnings = []
        
        # status الزامی است
        if 'status' not in resource:
            errors.append("Encounter باید status داشته باشد")
        
        # class الزامی است
        if 'class' not in resource:
            errors.append("Encounter باید class داشته باشد")
        
        return errors, warnings
    
    def _validate_observation(self, resource: Dict[str, Any]) -> tuple:
        """اعتبارسنجی منبع Observation"""
        errors = []
        warnings = []
        
        # status الزامی است
        if 'status' not in resource:
            errors.append("Observation باید status داشته باشد")
        
        # code الزامی است
        if 'code' not in resource:
            errors.append("Observation باید code داشته باشد")
        
        return errors, warnings


class FHIRCodeSystemMapper:
    """
    کلاس برای نگاشت کدهای داخلی به سیستم‌های کدگذاری FHIR
    """
    
    # نگاشت‌های پیش‌فرض
    CODE_SYSTEMS = {
        'condition': 'http://snomed.info/sct',
        'medication': 'http://www.nlm.nih.gov/research/umls/rxnorm',
        'procedure': 'http://www.ama-assn.org/go/cpt',
        'observation': 'http://loinc.org'
    }
    
    def map_code(
        self,
        internal_code: str,
        code_type: str,
        display_text: str = None
    ) -> Dict[str, Any]:
        """
        تبدیل کد داخلی به CodeableConcept FHIR
        """
        system = self.CODE_SYSTEMS.get(code_type, 'http://example.org/codes')
        
        codeable_concept = {
            'coding': [{
                'system': system,
                'code': internal_code
            }]
        }
        
        if display_text:
            codeable_concept['coding'][0]['display'] = display_text
            codeable_concept['text'] = display_text
        
        return codeable_concept
    
    def map_identifier(
        self,
        value: str,
        system: str = None,
        type_code: str = None
    ) -> Dict[str, Any]:
        """
        ساخت Identifier FHIR
        """
        identifier = {
            'value': value
        }
        
        if system:
            identifier['system'] = system
        
        if type_code:
            identifier['type'] = {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                    'code': type_code
                }]
            }
        
        return identifier