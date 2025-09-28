"""
URL patterns برای feedback app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ایجاد router برای ViewSets
router = DefaultRouter()
router.register(r'ratings', views.SessionRatingViewSet, basename='session-rating')
router.register(r'feedbacks', views.MessageFeedbackViewSet, basename='message-feedback')
router.register(r'surveys', views.SurveyViewSet, basename='survey')
router.register(r'settings', views.FeedbackSettingsViewSet, basename='feedback-settings')

app_name = 'feedback'

urlpatterns = [
    # Router URLs
    path('api/', include(router.urls)),
    
    # Additional endpoints
    path('api/analytics/', views.analytics_dashboard, name='analytics-dashboard'),
    
    # API endpoints for specific actions
    path('api/ratings/stats/', views.SessionRatingViewSet.as_view({'get': 'stats'}), name='rating-stats'),
    path('api/feedbacks/stats/', views.MessageFeedbackViewSet.as_view({'get': 'stats'}), name='feedback-stats'),
]