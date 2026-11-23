from collections import defaultdict
from datetime import date, timedelta
import re
from unicodedata import normalize
from apps.users.services.photo_reminders import archive_admission_date, assess_photo


RELEASE_CHECK_DAYS = 7


def release_check_window(today):
    return today + timedelta(days=1), today + timedelta(days=RELEASE_CHECK_DAYS)


def _text(value):
    return str(value).strip() if value is not None else ''


def _identity_key(value):
    return normalize('NFKC', value).casefold()


def _parse_date(value):
    match = re.fullmatch(
        r'(\d{4})[-./年](\d{1,2})[-./月](\d{1,2})(?:日|[ T]\d{2}:\d{2}:\d{2})?',
        value,
    )
    if match:
        try:
            return date(*map(int, match.groups()))
        except ValueError:
            pass
    return None


def archive_release_dates(archive):
    basic = archive.basic_info if isinstance(archive.basic_info, dict) else {}
    end = _text(archive.sentence_end)
    raw_end = _text(basic.get('zr'))
    return end, raw_end, _parse_date(end), _parse_date(raw_end)


def release_date_in_window(dates, range_start, range_end):
    return next((value for value in dates if value and range_start <= value <= range_end), None)


def build_release_check(archives, range_start, normalize_photo=str, *, range_end=None):
    range_end = range_end or range_start
    checked_on = range_start - timedelta(days=1)
    indexes = defaultdict(list)
    candidates = []
    undated = []

    for archive in archives:
        basic = archive.basic_info if isinstance(archive.basic_info, dict) else {}
        media = archive.media_info if isinstance(archive.media_info, list) else []
        name = _text(archive.prisoner_name)
        raw_name = _text(basic.get('xm'))
        number = _text(archive.prisoner_no)
        raw_number = _text(basic.get('bh'))
        photo_info = assess_photo(media, archive_admission_date(archive), checked_on, normalize_photo)
        photo = photo_info['url']
        keys = {
            ('档案库存在同名人员', _identity_key(name or raw_name)),
            ('档案库编号重复', _identity_key(number or raw_number)),
            ('档案库编号重复', _identity_key(raw_number)),
            ('档案库照片引用重复', photo),
        }
        identity = {
            'id': archive.pk,
            'prisoner_name': name or raw_name,
            'prisoner_no': number or raw_number,
            'photo_url': photo,
        }
        for key in keys:
            if key[1]:
                indexes[key].append(identity)

        if archive.is_released:
            continue

        end, raw_end, end_date, raw_end_date = archive_release_dates(archive)
        scheduled = release_date_in_window((end_date, raw_end_date), range_start, range_end)
        if not scheduled and (end_date or raw_end_date):
            continue

        sentence = _text(archive.sentence) or _text(basic.get('ypxq'))
        start = _text(archive.sentence_start)
        start_date = _parse_date(start)
        issues = []
        if not name:
            issues.append('缺少姓名')
        elif raw_name and _identity_key(name) != _identity_key(raw_name):
            issues.append('姓名与原始档案不一致')
        if not number:
            issues.append('缺少罪犯编号')
        elif raw_number and _identity_key(number) != _identity_key(raw_number):
            issues.append('罪犯编号与原始档案不一致')
        if not sentence:
            issues.append('缺少原判刑期')
        if not end:
            issues.append('缺少刑期止日')
        elif not end_date:
            issues.append('刑期止日格式错误')
        if raw_end and not raw_end_date:
            issues.append('原始档案刑期止日格式错误')
        if end_date and raw_end_date and end_date != raw_end_date:
            issues.append('刑期止日与原始档案不一致')
        if not start:
            issues.append('缺少刑期起日')
        elif not start_date:
            issues.append('刑期起日格式错误')
        elif scheduled and start_date > scheduled:
            issues.append('刑期起日晚于预释放日期')
        photo_issue = {
            'missing': '缺少档案照片',
            'invalid': '照片地址格式错误',
            'expired': '入监已满五年，请所属监区更新档案照片',
            'date_unknown': '入监日期待核实，请所属监区确认',
        }.get(photo_info['status'])
        if photo_issue:
            issues.append(photo_issue)

        row = {
            **identity,
            'prison_area': archive.prison_area,
            'sentence': sentence,
            'sentence_start': start,
            'sentence_end': end or raw_end,
            'raw_sentence_end': raw_end if raw_end != end else '',
            'release_date': scheduled.isoformat() if scheduled else None,
            'issues': issues,
            'related': [],
        }
        if scheduled:
            candidates.append((row, keys))
        else:
            undated.append(row)

    for row, keys in candidates:
        related = {}
        for issue, value in sorted(keys):
            for record in indexes.get((issue, value), []):
                if record['id'] == row['id']:
                    continue
                if issue not in row['issues']:
                    row['issues'].append(issue)
                related[record['id']] = record
        row['related'] = list(related.values())

    return {
        'date': range_start.isoformat(),
        'start_date': range_start.isoformat(),
        'end_date': range_end.isoformat(),
        'rows': sorted((row for row, _ in candidates), key=lambda row: row['release_date']),
        'undated': undated,
    }
