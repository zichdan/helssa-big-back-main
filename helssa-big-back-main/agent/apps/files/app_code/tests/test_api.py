"""
تست‌های API برای اپ فایل‌ها
"""

from io import BytesIO

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from files.app_code.models import StoredFile


User = get_user_model()


class FilesAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', password='p1')
        self.client.force_authenticate(self.user)

    def test_upload_and_list_file(self):
        url = '/api/files/stored-files/'
        content = BytesIO(b'hello world')
        content.name = 'hello.txt'

        response = self.client.post(url, {'file': content}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

        list_resp = self.client.get(url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(list_resp.data), 1)

    def test_delete_file(self):
        # ایجاد فایل
        content = BytesIO(b'bye')
        content.name = 'bye.txt'
        create_resp = self.client.post('/api/files/stored-files/', {'file': content}, format='multipart')
        file_id = create_resp.data['id']

        # حذف
        del_resp = self.client.delete(f'/api/files/stored-files/{file_id}/')
        self.assertIn(del_resp.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK])

