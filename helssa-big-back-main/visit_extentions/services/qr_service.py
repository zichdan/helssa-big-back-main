from __future__ import annotations

import qrcode
from io import BytesIO


def generate_qr_png_bytes(data: str, box_size: int = 8, border: int = 4) -> bytes:
    """
    تولید تصویر QR به صورت بایت‌های PNG
    """
    qr = qrcode.QRCode(version=None, box_size=box_size, border=border)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

