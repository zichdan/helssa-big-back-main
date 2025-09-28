"""
Orchestrator bridge for Notifications app
"""

from typing import Dict, Any
from app_standards.four_cores import CentralOrchestrator


class NotificationsOrchestrator(CentralOrchestrator):
    """
    هماهنگ‌کننده اختصاصی اپ اعلان‌ها بر پایه الگوی استاندارد
    """

    def execute_send_notification(self, data: Dict[str, Any], user: Any):  # type: ignore[name-defined]
        """
        اجرای فرآیند ارسال اعلان با نام گردش‌کار استاندارد
        """
        return self.execute_workflow('send_notification', data, user)

