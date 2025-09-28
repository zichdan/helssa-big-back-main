from __future__ import annotations

import os
from kavenegar import KavenegarAPI, APIException, HTTPException


def send_download_link(phone_number: str, download_url: str, template: str | None = None) -> None:
    """
    ارسال پیامک حاوی لینک دانلود با کاوه‌نگار
    """
    api_key = os.environ.get('KAVENEGAR_API_KEY')
    sender = os.environ.get('KAVENEGAR_SENDER', '')
    template_name = template or os.environ.get('KAVENEGAR_DOWNLOAD_TEMPLATE', 'download_link')
    if not api_key:
        raise RuntimeError('KAVENEGAR_API_KEY is not configured')

    api = KavenegarAPI(api_key)
    try:
        # استفاده از پیامک ساده (در صورت نیاز می‌توان VerifyLookup به کار برد)
        params = {
            'sender': sender,
            'receptor': phone_number,
            'message': f'لینک دانلود شما: {download_url}',
        }
        api.sms_send(params)
    except (APIException, HTTPException) as exc:
        raise RuntimeError(f'Kavenegar error: {exc}')

