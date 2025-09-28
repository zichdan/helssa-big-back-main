from typing import List, Dict, Optional
import hashlib
import magic
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async

from ..models import Encounter, EncounterFile
from ..utils.encryption import encrypt_data, decrypt_data


class InvalidFileTypeError(Exception):
    """خطای نوع فایل نامعتبر"""
    pass


class SecurityError(Exception):
    """خطای امنیتی"""
    pass


class EncounterFileManager:
    """مدیریت فایل‌های ملاقات"""
    
    def __init__(self):
        self.allowed_types = {
            'audio': ['audio/mpeg', 'audio/wav', 'audio/webm', 'audio/ogg'],
            'image': ['image/jpeg', 'image/png', 'image/gif'],
            'document': ['application/pdf', 'application/msword',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'video': ['video/mp4', 'video/webm'],
            'lab_result': ['application/pdf', 'image/jpeg', 'image/png'],
            'radiology': ['image/dicom', 'image/jpeg', 'image/png', 'application/pdf']
        }
        
    async def upload_encounter_file(
        self,
        encounter_id: str,
        file_data: bytes,
        file_name: str,
        file_type: str,
        uploaded_by: str,
        description: str = ""
    ) -> EncounterFile:
        """آپلود فایل مرتبط با ملاقات"""
        
        encounter = await sync_to_async(Encounter.objects.get)(id=encounter_id)
        
        # بررسی نوع فایل
        mime_type = magic.from_buffer(file_data, mime=True)
        if not self._is_allowed_file_type(mime_type, file_type):
            raise InvalidFileTypeError(
                f"نوع فایل {mime_type} برای {file_type} مجاز نیست"
            )
            
        # اسکن امنیتی
        if not await self._scan_file_security(file_data):
            raise SecurityError("فایل از نظر امنیتی مشکل دارد")
            
        # رمزنگاری
        encrypted_data = await encrypt_data(
            file_data,
            encounter.encryption_key
        )
        
        # تولید hash برای تشخیص تکراری
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # بررسی تکراری بودن
        existing = await sync_to_async(
            EncounterFile.objects.filter(
                encounter=encounter,
                file_hash=file_hash
            ).first
        )()
        
        if existing:
            return existing
            
        # آپلود به storage
        storage_path = f"encounters/{encounter_id}/files/{file_type}/{file_name}"
        file_url = await self._upload_to_storage(
            storage_path,
            encrypted_data,
            content_type=mime_type
        )
        
        # ایجاد رکورد
        encounter_file = await sync_to_async(EncounterFile.objects.create)(
            encounter=encounter,
            file_name=file_name,
            file_type=file_type,
            mime_type=mime_type,
            file_url=file_url,
            file_size=len(file_data),
            file_hash=file_hash,
            uploaded_by_id=uploaded_by,
            is_encrypted=True,
            description=description,
            metadata={
                'original_name': file_name,
                'upload_timestamp': timezone.now().isoformat()
            }
        )
        
        return encounter_file
        
    async def get_encounter_files(
        self,
        encounter_id: str,
        file_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """دریافت فایل‌های ملاقات"""
        
        encounter = await sync_to_async(Encounter.objects.get)(id=encounter_id)
        
        # بررسی دسترسی
        if user_id:
            has_access = await self._check_file_access(
                encounter, user_id
            )
            if not has_access:
                raise PermissionError("شما دسترسی به این فایل‌ها ندارید")
                
        # Query files
        query = EncounterFile.objects.filter(encounter=encounter)
        if file_type:
            query = query.filter(file_type=file_type)
            
        files = await sync_to_async(list)(
            query.order_by('-created_at')
        )
        
        # آماده‌سازی برای نمایش
        result = []
        for file in files:
            # تولید لینک موقت دانلود
            download_url = await self._generate_download_url(
                file, user_id
            )
            
            result.append({
                'id': str(file.id),
                'name': file.file_name,
                'type': file.file_type,
                'type_display': file.get_file_type_display(),
                'mime_type': file.mime_type,
                'size': file.file_size,
                'size_mb': file.file_size_mb,
                'download_url': download_url,
                'description': file.description,
                'uploaded_at': file.created_at.isoformat(),
                'uploaded_by': await self._get_uploader_name(file.uploaded_by_id)
            })
            
        return result
        
    async def download_file(
        self,
        file_id: str,
        user_id: str
    ) -> Dict:
        """دانلود فایل"""
        
        file = await sync_to_async(
            EncounterFile.objects.select_related('encounter').get
        )(id=file_id)
        
        # بررسی دسترسی
        has_access = await self._check_file_access(
            file.encounter, user_id
        )
        if not has_access:
            raise PermissionError("شما دسترسی به این فایل ندارید")
            
        # دانلود از storage
        encrypted_data = await self._download_from_storage(file.file_url)
        
        # رمزگشایی
        decrypted_data = await decrypt_data(
            encrypted_data,
            file.encounter.encryption_key
        )
        
        return {
            'data': decrypted_data,
            'filename': file.file_name,
            'mime_type': file.mime_type,
            'size': file.file_size
        }
        
    async def delete_file(
        self,
        file_id: str,
        deleted_by: str
    ) -> bool:
        """حذف فایل"""
        
        file = await sync_to_async(
            EncounterFile.objects.select_related('encounter').get
        )(id=file_id)
        
        # بررسی دسترسی حذف (فقط پزشک یا آپلودکننده)
        if deleted_by not in [str(file.encounter.doctor_id), str(file.uploaded_by_id)]:
            raise PermissionError("شما اجازه حذف این فایل را ندارید")
            
        # حذف از storage
        await self._delete_from_storage(file.file_url)
        
        # حذف رکورد
        await sync_to_async(file.delete)()
        
        return True
        
    async def get_file_statistics(
        self,
        encounter_id: str
    ) -> Dict:
        """آمار فایل‌های ملاقات"""
        
        files = await sync_to_async(list)(
            EncounterFile.objects.filter(
                encounter_id=encounter_id
            ).values('file_type', 'file_size')
        )
        
        # محاسبه آمار
        stats = {
            'total_count': len(files),
            'total_size': sum(f['file_size'] for f in files),
            'by_type': {}
        }
        
        # آمار بر اساس نوع
        for file in files:
            file_type = file['file_type']
            if file_type not in stats['by_type']:
                stats['by_type'][file_type] = {
                    'count': 0,
                    'size': 0
                }
            stats['by_type'][file_type]['count'] += 1
            stats['by_type'][file_type]['size'] += file['file_size']
            
        # تبدیل به مگابایت
        stats['total_size_mb'] = round(stats['total_size'] / (1024 * 1024), 2)
        for type_stats in stats['by_type'].values():
            type_stats['size_mb'] = round(type_stats['size'] / (1024 * 1024), 2)
            
        return stats
        
    def _is_allowed_file_type(self, mime_type: str, file_type: str) -> bool:
        """بررسی مجاز بودن نوع فایل"""
        
        allowed_mimes = self.allowed_types.get(file_type, [])
        return mime_type in allowed_mimes
        
    async def _scan_file_security(self, file_data: bytes) -> bool:
        """اسکن امنیتی فایل"""
        
        # TODO: اتصال به آنتی‌ویروس یا سرویس اسکن
        
        # بررسی‌های پایه
        # حداکثر حجم: 100MB
        if len(file_data) > 100 * 1024 * 1024:
            return False
            
        # بررسی فایل‌های اجرایی
        dangerous_signatures = [
            b'MZ',  # Windows executables
            b'\x7fELF',  # Linux executables
            b'#!/',  # Scripts
        ]
        
        for sig in dangerous_signatures:
            if file_data.startswith(sig):
                return False
                
        return True
        
    async def _check_file_access(
        self,
        encounter: Encounter,
        user_id: str
    ) -> bool:
        """بررسی دسترسی به فایل‌ها"""
        
        # بیمار و پزشک دسترسی دارند
        if user_id in [str(encounter.patient_id), str(encounter.doctor_id)]:
            return True
            
        # TODO: بررسی دسترسی‌های دیگر
        
        return False
        
    async def _generate_download_url(
        self,
        file: EncounterFile,
        user_id: Optional[str]
    ) -> str:
        """تولید لینک دانلود موقت"""
        
        # تولید توکن دانلود
        token_data = {
            'file_id': str(file.id),
            'user_id': user_id,
            'expires': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        token = jwt.encode(
            token_data,
            settings.SECRET_KEY,
            algorithm='HS256'
        )
        
        return f"/api/encounters/files/download/?token={token}"
        
    async def _get_uploader_name(self, uploader_id: str) -> str:
        """دریافت نام آپلودکننده"""
        
        # TODO: دریافت از UnifiedUser
        return "کاربر سیستم"
        
    async def _upload_to_storage(
        self,
        path: str,
        data: bytes,
        content_type: str
    ) -> str:
        """آپلود به MinIO"""
        
        # TODO: اتصال به MinIO service
        return f"https://storage.helssa.ir/{path}"
        
    async def _download_from_storage(self, url: str) -> bytes:
        """دانلود از MinIO"""
        
        # TODO: اتصال به MinIO service
        return b''
        
    async def _delete_from_storage(self, url: str) -> bool:
        """حذف از MinIO"""
        
        # TODO: اتصال به MinIO service
        return True