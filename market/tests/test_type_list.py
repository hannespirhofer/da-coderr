from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

class TestUserByType(APITestCase):

    def set_up(self):
        user = User.objects.create_user(username='testuser', password='pass')
        self.client.force_login(user=user)

    def test_anon(self):
        url_customer = reverse('customer-list')
        url_business = reverse('business-list')
        resp_customer = self.client.get(url_customer)
        resp_business = self.client.get(url_business)
        self.assertEqual(resp_customer.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp_business.status_code, HTTP_401_UNAUTHORIZED)

    def test_customer_users(self):
        self.set_up()
        url = reverse('customer-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, HTTP_200_OK)

    def test_business_users(self):
        self.set_up()
        url = reverse('business-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, HTTP_200_OK)