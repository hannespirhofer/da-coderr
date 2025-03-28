from rest_framework.test import APITestCase
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_405_METHOD_NOT_ALLOWED
from django.urls import reverse
from django.contrib.auth.models import User

class LoginTest(APITestCase):
    url = reverse('login')

    def test_get_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_login_empty(self):
        data = {}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_post_login_correct(self):
        User.objects.create_user(username='testuser', password='testpassword')
        data = {
            "username": "testuser",
            "password": "testpassword"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertIn('token', response.data)
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('user_id', response.data)