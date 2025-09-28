# برنامه پیاده‌سازی اپ Files

- هدف: مدیریت آپلود و مدیریت فایل‌های کاربران
- هسته‌ها: استفاده از API Ingress استاندارد در آینده (نیاز خاصی فعلاً نیست)
- API:
  - POST /api/files/stored-files/
  - GET /api/files/stored-files/
  - GET /api/files/stored-files/{id}/
  - DELETE /api/files/stored-files/{id}/

- مدل‌ها: `StoredFile` مبتنی بر `FileAttachmentModel`
- امنیت: JWT، محدودیت نرخ استاندارد
- Deployment: `deployment/settings_additions.py`, `deployment/urls_additions.py`