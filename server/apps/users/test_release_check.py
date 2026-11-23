from datetime import date, timedelta
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import PrisonerArchive, User

from apps.users.services.release_check import build_release_check, release_check_window


class ReleaseCheckTests(SimpleTestCase):
    target = date(2026, 11, 17)

    def archive(self, pk=1, **fields):
        return SimpleNamespace(**{
            'pk': pk, 'prisoner_no': str(pk), 'prisoner_name': '测试人员',
            'prison_area': '', 'sentence': '三年', 'sentence_start': '2023-11-18',
            'sentence_end': '2026年11月17日', 'basic_info': {}, 'is_released': False,
            'entry_date': '2023-11-18', 'media_info': [{'xp': 'https://example.test/portrait.jpg'}],
            **fields,
        })

    def test_target_date_and_archive_conflicts(self):
        report = build_release_check([
            self.archive(prisoner_no='Ａ01'),
            self.archive(2, prisoner_no='a01', sentence_end='2026-11-18'),
        ], self.target)
        self.assertEqual([r['id'] for r in report['rows']], [1])
        self.assertEqual(set(report['rows'][0]['issues']), {
            '档案库存在同名人员', '档案库编号重复', '档案库照片引用重复',
        })
        self.assertEqual(report['rows'][0]['related'][0]['id'], 2)

    def test_missing_photo_and_conflicting_sentence_fields(self):
        report = build_release_check([
            self.archive(sentence='', sentence_start='2026-11-18',
                         sentence_end='2026-11-19', media_info=[],
                         basic_info={'zr': '2026/11/17', 'xm': '姓名不一致'}),
            self.archive(2, prisoner_name='另一位测试人员', sentence_end='2026-02-30'),
        ], self.target)
        self.assertEqual(set(report['rows'][0]['issues']), {
            '姓名与原始档案不一致', '缺少原判刑期', '刑期止日与原始档案不一致',
            '刑期起日晚于预释放日期', '缺少档案照片',
        })
        self.assertEqual([r['id'] for r in report['undated']], [2])

    def test_old_record_can_use_raw_date_and_reject_invalid_photo(self):
        report = build_release_check([
            self.archive(sentence_end='', basic_info={'zr': '2026.11.17'},
                         media_info=[{'xp': 'javascript:alert(1)'}]),
        ], self.target)
        self.assertEqual(report['rows'][0]['issues'], ['缺少刑期止日', '照片地址格式错误'])
        self.assertEqual(report['rows'][0]['photo_url'], '')

    def test_week_includes_first_and_seventh_day_and_excludes_outside_dates(self):
        start, end = release_check_window(date(2026, 11, 18))
        report = build_release_check([
            self.archive(1, sentence_end='2026-11-25', basic_info={'zr': '2026-11-24'}),
            self.archive(2, sentence_end='2026-11-19'),
            self.archive(3, sentence_end='2026-11-18'),
            self.archive(4, sentence_end='2026-11-26'),
            self.archive(5, sentence_end='', basic_info={'zr': '2026-11-22'}),
        ], start, range_end=end)
        self.assertEqual((report['start_date'], report['end_date']), ('2026-11-19', '2026-11-25'))
        self.assertEqual([(r['id'], r['release_date']) for r in report['rows']], [
            (2, '2026-11-19'), (5, '2026-11-22'), (1, '2026-11-25'),
        ])
        self.assertIn('刑期止日与原始档案不一致', report['rows'][-1]['issues'])


class ReleaseReviewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='reviewer')
        self.client.force_authenticate(self.user)
        self.target = timezone.localdate() + timedelta(days=1)
        self.archive = PrisonerArchive.objects.create(
            prisoner_no='REVIEW-001', prisoner_name='测试人员', sentence_end=self.target.isoformat(),
        )
        self.url = reverse('release_check')
        self.payload = {
            'archive_id': self.archive.pk, 'release_date': self.target.isoformat(),
            'decision': 'needs_review', 'note': '请复核照片',
        }

    def test_save_read_and_update(self):
        self.assertEqual(self.client.post(self.url, self.payload).json()['code'], 1)
        report = self.client.get(self.url).json()['data']
        review = report['rows'][0]['review']
        self.assertEqual(review['note'], '请复核照片')
        self.assertEqual(review['reviewer'], 'reviewer')
        self.assertTrue(review['reviewed_at'])
        result = self.client.post(self.url, {**self.payload, 'decision': 'verified', 'note': ''})
        self.assertEqual(result.json()['data']['decision'], 'verified')
        self.assertEqual(self.client.get(self.url).json()['data']['rows'][0]['review']['decision'], 'verified')

    def test_reject_stale_date_released_person_and_missing_note(self):
        for change in ({'release_date': timezone.localdate().isoformat()}, {'note': '   '}):
            self.assertEqual(self.client.post(self.url, {**self.payload, **change}).json()['code'], 0)
        self.archive.is_released = True
        self.archive.save(update_fields=['is_released'])
        self.assertEqual(self.client.post(self.url, self.payload).json()['code'], 0)

    def test_anonymous_user_cannot_save(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(self.url, self.payload).json()['code'], 0)

    def test_save_on_seventh_day_and_reload_by_person_release_date(self):
        seventh_day = self.target + timedelta(days=6)
        eligible = PrisonerArchive.objects.create(prisoner_no='REVIEW-007', sentence_end=seventh_day.isoformat())
        invalid = {**self.payload, 'archive_id': eligible.pk}
        self.assertEqual(self.client.post(self.url, invalid).json()['code'], 0)
        valid = {**invalid, 'release_date': seventh_day.isoformat()}
        self.assertEqual(self.client.post(self.url, valid).json()['code'], 1)
        report = self.client.get(self.url).json()['data']
        self.assertIsNone(report['rows'][0]['review'])
        self.assertEqual(report['rows'][1]['release_date'], seventh_day.isoformat())
        self.assertEqual(report['rows'][1]['review']['reviewer'], 'reviewer')
