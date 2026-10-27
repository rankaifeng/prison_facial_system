"""
监区字典
前端传入 id，后端自动转换为 name
"""

PRISON_AREAS = [
    {'id': 1, 'name': '一监区'},
    {'id': 2, 'name': '二监区'},
    {'id': 3, 'name': '三监区'},
    {'id': 4, 'name': '四监区'},
    {'id': 5, 'name': '五监区'},
    {'id': 6, 'name': '六监区'},
    {'id': 7, 'name': '七监区'},
]


def get_prison_area_name(prison_area_id):
    """根据 ID 或名称获取监区名称"""
    if not prison_area_id:
        return ''

    # 如果是纯数字字符串，尝试作为 ID 查询
    try:
        int_id = int(prison_area_id)
        for area in PRISON_AREAS:
            if area['id'] == int_id:
                return area['name']
        # 没找到对应的 ID，返回原值
        return ''
    except (ValueError, TypeError):
        # 不是数字，当作名称直接返回
        return prison_area_id


def get_prison_area_id(prison_area_name):
    """根据名称获取监区 ID"""
    for area in PRISON_AREAS:
        if area['name'] == prison_area_name:
            return area['id']
    return None


def get_all_prison_areas():
    """获取所有监区列表"""
    return PRISON_AREAS


def get_prison_area_dict():
    """获取监区字典 {id: name}"""
    return {area['id']: area['name'] for area in PRISON_AREAS}


def split_prison_ids(value):
    """
    把监区值拆成列表，兼容单值（"1"）和多值（"1,2"），非数字原样保留
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [p.strip() for p in str(value).split(',') if p.strip()]


def get_prison_area_names(prison_ids):
    """根据 ID 列表获取逗号分隔的监区名称"""
    names = []
    for pid in split_prison_ids(prison_ids):
        name = get_prison_area_name(pid)
        if name and name not in names:
            names.append(name)
    return ','.join(names)


def expand_prison_area_values(value):
    """
    把监区值（单ID、多ID逗号串、名称）展开为 ID+名称的去重列表，用于 __in 查询
    """
    values = []
    for v in split_prison_ids(value):
        if v not in values:
            values.append(v)
        name = get_prison_area_name(v)
        if name and name != v and name not in values:
            values.append(name)
    return values