from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import User


class AccountAreaTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user(username='admin-test', role='admin'))
        self.user = User.objects.create_user(username='area-test', prison_id='1', prison_name='一监区')
        self.url = reverse('account_update')

    def test_multipart_update_keeps_all_selected_areas(self):
        result = self.client.post(self.url, {'id': self.user.pk, 'prison_ids': [2, 3, 7]}, format='multipart')
        self.assertEqual(result.json()['code'], 1)
        records = self.client.get(reverse('account_list'), {'username': self.user.username}).json()['data']
        self.assertEqual(records[0]['prison_id'], '2,3,7')
        self.assertEqual(records[0]['prison_name'], '二监区,三监区,七监区')

    def test_json_list_and_legacy_single_id(self):
        for values, expected in [({'prison_ids': [1, 4]}, '1,4'), ({'prison_id': '2'}, '2')]:
            result = self.client.post(self.url, {'id': self.user.pk, **values}, format='json')
            self.assertEqual(result.json()['code'], 1)
            self.user.refresh_from_db()
            self.assertEqual(self.user.prison_id, expected)
