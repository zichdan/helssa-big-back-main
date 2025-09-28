"""
ویوهای اپلیکیشن
Application Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from app_standards.four_cores import APIIngressCore, CentralOrchestrator

# ویوهای اپلیکیشن را اینجا تعریف کنید
