import re
from calendar import monthrange
from datetime import date
from urllib.parse import urlsplit


PHOTO_AGE_YEARS = 5
PHOTO_ACTIONS = {
    'missing': '请所属监区补采并录入正面照',
    'invalid': '请所属监区核查照片地址或重新录入正面照',
    'expired': '请所属监区重新采集并更新正面照',
    'date_unknown': '请所属监区核实或补录入监日期',
}


def archive_admission_date(archive):
    basic = archive.basic_info if isinstance(archive.basic_info, dict) else {}
    for value in (archive.entry_date, basic.get('rjrq')):
        match = re.fullmatch(
            r'(\d{4})[-./年](\d{1,2})[-./月](\d{1,2})(?:日|[ T]\d{2}:\d{2}:\d{2})?',
            str(value or '').strip(),
        )
        if match:
            try:
                return date(*map(int, match.groups()))
            except ValueError:
                continue
    return None


def assess_photo(media, entry_date, today, normalize_photo=str):
    """从档案选择正面照片，并按入监日期计算五周年。"""
    admission = entry_date.isoformat() if entry_date else ''
    portraits = []
    has_reference = False
    for item in media if isinstance(media, list) else []:
        if not isinstance(item, dict):
            continue
        kind = str(item.get('mtbmm') or '').strip()
        if any(marker in kind for marker in ('侧面', '背面', '全身')):
            continue
        raw_url = str(item.get('xp') or '').strip()
        if not raw_url:
            continue
        has_reference = True
        try:
            parts = urlsplit(normalize_photo(raw_url))
            remote = parts.scheme in ('http', 'https') and parts.hostname and not parts.username
            local = not parts.scheme and not parts.netloc and parts.path.startswith('/media/')
            if not (remote or local):
                continue
        except ValueError:
            continue
        portraits.append(('正面' in kind, parts._replace(fragment='').geturl()))

    if not portraits:
        return {'status': 'invalid' if has_reference else 'missing', 'entry_date': admission, 'url': ''}

    _, url = max(portraits, key=lambda entry: entry[0])
    status = 'date_unknown'
    if entry_date and entry_date <= today:
        year = entry_date.year + PHOTO_AGE_YEARS
        day = min(entry_date.day, monthrange(year, entry_date.month)[1])
        anniversary = date(year, entry_date.month, day)
        status = 'expired' if anniversary <= today else 'current'
    return {'status': status, 'entry_date': admission, 'url': url}
