from datetime import date

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import PrisonerArchive, User
from apps.users.services.photo_reminders import assess_photo


def portrait(kind='正面像'):
    return {'mtbmm': kind, 'xp': 'http://photos.example/photo.jpg'}


class PhotoAssessmentTests(SimpleTestCase):
    def test_missing_and_age(self):
        today = date(2026, 11, 16)
        self.assertEqual(assess_photo([], None, today)['status'], 'missing')
        self.assertEqual(assess_photo([portrait('侧面像')], date(2020, 1, 1), today)['status'], 'missing')
        self.assertEqual(assess_photo([portrait()], date(2021, 11, 16), today)['status'], 'expired')
        self.assertEqual(assess_photo([portrait()], date(2021, 11, 17), today)['status'], 'current')
        self.assertEqual(assess_photo([portrait()], date(2026, 11, 17), today)['status'], 'date_unknown')
        self.assertEqual(assess_photo([portrait()], None, today)['status'], 'date_unknown')

    def test_leap_day_anniversary(self):
        result = assess_photo([portrait()], date(2020, 2, 29), date(2025, 2, 28))
        self.assertEqual(result['status'], 'expired')
        self.assertEqual(result['entry_date'], '2020-02-29')


class PhotoReminderTests(TestCase):
    def test_area_options_remain_available_when_no_reminders_match(self):
        client = APIClient()
        user = User.objects.create_user(username='areas', prison_id='1,3')
        client.force_authenticate(user)
        response = client.get(reverse('archive_photo_reminders')).json()
        self.assertEqual(response['data'], [])
        self.assertEqual(response['areas'], ['一监区', '三监区'])
        user.role = 'admin'
        response = client.get(reverse('archive_photo_reminders')).json()
        self.assertEqual(response['data'], [])
        self.assertEqual(len(response['areas']), 7)

    def test_monitoring_is_scoped_to_assigned_areas(self):
        client = APIClient()
        user = User.objects.create_user(username='area-user', prison_id='1')
        client.force_authenticate(user)
        for number, area, released in [('QA-1', '一监区', False), ('QA-2', '二监区', False),
                                       ('QA-3', '一监区', True)]:
            PrisonerArchive.objects.create(prisoner_no=number, prison_area=area, is_released=released)
        report = client.get(reverse('archive_photo_reminders')).json()['data']
        self.assertEqual([row['prisoner_no'] for row in report], ['QA-1'])
        self.assertEqual(report[0]['status'], 'missing')
        user.role = 'admin'
        report = client.get(reverse('archive_photo_reminders')).json()['data']
        self.assertEqual({row['prisoner_no'] for row in report}, {'QA-1', 'QA-2'})

    def test_fallback_to_original_admission_date(self):
        client = APIClient()
        client.force_authenticate(User.objects.create_user(username='admin', role='admin'))
        PrisonerArchive.objects.create(
            prisoner_no='QA-FALLBACK', entry_date='', basic_info={'rjrq': '2010.11.16'},
            media_info=[portrait()],
        )
        report = client.get(reverse('archive_photo_reminders')).json()['data']
        self.assertEqual(report[0]['status'], 'expired')
        self.assertEqual(report[0]['entry_date'], '2010-11-16')
