"""
سریالایزرهای اپلیکیشن اعلان‌ها
Application Serializers for Notifications
"""

from rest_framework import serializers


class NotificationRequestSerializer(serializers.Serializer):
    """
    سریالایزر درخواست ارسال اعلان
    """

    notification_type = serializers.ChoiceField(
        choices=[('sms', 'sms'), ('email', 'email'), ('push', 'push'), ('in_app', 'in_app')]
    )
    title = serializers.CharField(max_length=200)
    content = serializers.CharField(max_length=5000)
    priority = serializers.ChoiceField(
        choices=[('low', 'low'), ('normal', 'normal'), ('high', 'high'), ('urgent', 'urgent')],
        required=False,
        default='normal'
    )
    scheduled_for = serializers.DateTimeField(required=False, allow_null=True)
    metadata = serializers.DictField(required=False)

    def validate(self, attrs):
        """
        اعتبارسنجی ترکیبی فیلدها
        """
        if attrs['notification_type'] in ['sms', 'push'] and len(attrs['content']) > 1000:
            raise serializers.ValidationError('طول محتوای اعلان برای این نوع بیش از حد مجاز است')
        return attrs


class NotificationResponseSerializer(serializers.Serializer):
    """
    سریالایزر پاسخ ارسال اعلان
    """

    queued = serializers.BooleanField()
    notification_type = serializers.CharField()
    title = serializers.CharField()
    content = serializers.CharField()
    priority = serializers.CharField()
    scheduled_for = serializers.DateTimeField(allow_null=True)
    reference_id = serializers.CharField()

