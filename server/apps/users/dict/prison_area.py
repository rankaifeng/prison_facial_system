"""
分监区字典
前端传入 id，后端自动转换为 name
"""

PRISON_AREAS = [
    {'id': 1, 'name': '分监区一'},
    {'id': 2, 'name': '分监区二'},
    {'id': 3, 'name': '分监区三'},
    {'id': 4, 'name': '分监区四'},
    {'id': 5, 'name': '分监区五'},
    {'id': 6, 'name': '分监区六'},
    {'id': 7, 'name': '分监区七'},
]


def get_prison_area_name(prison_area_id):
    """根据 ID 获取分监区名称"""
    if not prison_area_id:
        return ''
    try:
        prison_area_id = str(int(prison_area_id))
    except (ValueError, TypeError):
        return ''
    for area in PRISON_AREAS:
        if str(area['id']) == prison_area_id:
            return area['name']
    return ''


def get_prison_area_id(prison_area_name):
    """根据名称获取分监区 ID"""
    for area in PRISON_AREAS:
        if area['name'] == prison_area_name:
            return area['id']
    return None


def get_all_prison_areas():
    """获取所有分监区列表"""
    return PRISON_AREAS


def get_prison_area_dict():
    """获取分监区字典 {id: name}"""
    return {area['id']: area['name'] for area in PRISON_AREAS}