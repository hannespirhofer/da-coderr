from rest_framework.test import APITestCase
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED
from rest_framework.test import force_authenticate
from django.urls import reverse
from django.contrib.auth.models import User

from market.models import MarketUser

class ProfileTest(APITestCase):

    def set_up(self):
        self.user = User.objects.create_user(username='user', password='pass', email='mail@mail.de')
        self.marketuser = MarketUser.objects.create(user = self.user, type='customer')
        self.url = reverse("profile-detail", kwargs={'pk': self.marketuser.pk})

    def test_anon_get_profile(self):
        self.set_up()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_anon_check_options(self):
        self.set_up()
        response = self.client.options(self.url)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_user_check_options(self):
        self.set_up()
        self.client.force_login(user=self.user)
        response = self.client.options(self.url)
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_get_profile(self):
        self.set_up()
        self.client.force_login(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_patch_profile_user(self):
        data = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "location": "Berlin",
            "tel": "987654321",
            "description": "Updated business description",
            "working_hours": "10-18",
            "email": "new_email@business.de"
        }
        self.set_up()
        self.client.force_login(user=self.user)
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        expected_keys = [
            'user',
            'username',
            'first_name',
            'last_name',
            'file',
            'location',
            'tel',
            'description',
            'working_hours',
            'type',
            'email',
            'created_at'
        ]
        for key in expected_keys:
            self.assertIn(key, response.data)
        self.assertEqual(response.data["email"], "new_email@business.de")

    def test_authorized_not_owner(self):
        #setup owner
        self.set_up()

        otheruser = User.objects.create_user(username='other', password='password')
        self.client.force_login(user=otheruser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)








