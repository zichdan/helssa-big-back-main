import base64
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Union


def generate_encryption_key() -> str:
    """تولید کلید رمزنگاری جدید"""
    key = Fernet.generate_key()
    return base64.urlsafe_b64encode(key).decode()


def _get_fernet_instance(key: str) -> Fernet:
    """ایجاد instance از Fernet با کلید داده شده"""
    try:
        # اگر کلید در فرمت base64 است
        key_bytes = base64.urlsafe_b64decode(key.encode())
    except:
        # اگر کلید raw bytes است
        key_bytes = key.encode()
        
    # اطمینان از طول صحیح کلید (32 بایت)
    if len(key_bytes) == 32:
        return Fernet(base64.urlsafe_b64encode(key_bytes))
    else:
        # تولید کلید 32 بایتی از کلید ورودی
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'helssa_salt_2024',  # Salt ثابت برای consistency
            iterations=100000,
        )
        derived_key = kdf.derive(key_bytes)
        return Fernet(base64.urlsafe_b64encode(derived_key))


async def encrypt_data(data: Union[str, bytes], key: str) -> str:
    """رمزنگاری داده با کلید داده شده"""
    
    if isinstance(data, str):
        data = data.encode()
        
    fernet = _get_fernet_instance(key)
    encrypted = fernet.encrypt(data)
    
    return base64.urlsafe_b64encode(encrypted).decode()


async def decrypt_data(encrypted_data: str, key: str) -> bytes:
    """رمزگشایی داده با کلید داده شده"""
    
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
    fernet = _get_fernet_instance(key)
    decrypted = fernet.decrypt(encrypted_bytes)
    
    return decrypted


def generate_secure_token(length: int = 32) -> str:
    """تولید توکن امن تصادفی"""
    return secrets.token_urlsafe(length)


def hash_data(data: str) -> str:
    """تولید hash از داده"""
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()


def verify_hash(data: str, hash_value: str) -> bool:
    """بررسی صحت hash"""
    return hash_data(data) == hash_value