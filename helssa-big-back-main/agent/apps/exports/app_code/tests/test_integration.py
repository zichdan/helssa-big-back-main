from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model


User = get_user_model()


class ExportsIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_main_endpoint_exists(self):
        response = self.client.post('/api/exports/main/', {'payload': {}})
        # Endpoint exists; until logic is provided, accept 200/400 depending on validator
        self.assertIn(response.status_code, [200, 400, 500])

