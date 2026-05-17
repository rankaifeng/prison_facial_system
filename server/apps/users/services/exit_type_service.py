import logging
from apps.users.repositories import ExitTypeRepository
from .base_service import BaseService

logger = logging.getLogger(__name__)


class ExitTypeService(BaseService):

    @staticmethod
    def _serialize(item, children=None):
        return {
            'id': item.id,
            'key': item.id,
            'type_name': item.type_name,
            'parent_id': item.parent_id,
            'parent_name': item.parent.type_name if item.parent else '',
            'level': item.level,
            'sort_order': item.sort_order,
            'status': item.status,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            'updated_at': item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else '',
            'children': children or [],
        }

    @staticmethod
    def _build_tree(items, keyword=''):
        by_parent = {}
        for item in items:
            by_parent.setdefault(item.parent_id, []).append(item)

        normalized_keyword = (keyword or '').strip().lower()

        def walk(parent_id=None, ancestor_matched=False):
            nodes = []
            for item in by_parent.get(parent_id, []):
                self_matched = not normalized_keyword or normalized_keyword in item.type_name.lower()
                child_nodes = walk(item.id, ancestor_matched or self_matched)

                if not normalized_keyword or self_matched or child_nodes or ancestor_matched:
                    if normalized_keyword and self_matched:
                        child_nodes = walk(item.id, True)
                    nodes.append(ExitTypeService._serialize(item, child_nodes))
            return nodes

        return walk(None)

    @staticmethod
    def list_exit_types(type_name=''):
        items = list(ExitTypeRepository.get_all().select_related('parent'))
        tree = ExitTypeService._build_tree(items, type_name)
        return True, '获取成功', tree

    @staticmethod
    def create_exit_type(type_name, parent_id=None, sort_order=0, status='active'):
        type_name = (type_name or '').strip()
        if not type_name:
            return False, '出监原因不能为空', None

        parent = None
        if parent_id:
            parent = ExitTypeRepository.get_by_id(parent_id)
            if not parent:
                return False, '上级出监原因不存在', None

        if ExitTypeRepository.exists_by_sibling_name(type_name, parent.id if parent else None):
            return False, '同级出监原因已存在', None

        item = ExitTypeRepository.create(
            type_name=type_name,
            parent=parent,
            level=(parent.level + 1) if parent else 1,
            sort_order=sort_order or 0,
            status=status or 'active',
        )
        logger.info(f"Exit type created: id={item.id}, name={type_name}, parent_id={parent_id}")
        return True, '新增成功', ExitTypeService._serialize(item)

    @staticmethod
    def update_exit_type(exit_type_id, type_name, parent_id=None, sort_order=0, status='active'):
        item = ExitTypeRepository.get_by_id(exit_type_id)
        if not item:
            return False, '出监原因不存在', None

        type_name = (type_name or '').strip()
        if not type_name:
            return False, '出监原因不能为空', None

        parent = None
        if parent_id:
            parent = ExitTypeRepository.get_by_id(parent_id)
            if not parent:
                return False, '上级出监原因不存在', None
            if parent.id == item.id:
                return False, '上级不能选择自己', None
            if ExitTypeService._is_descendant(parent, item.id):
                return False, '上级不能选择自己的下级', None

        if ExitTypeRepository.exists_by_sibling_name(type_name, parent.id if parent else None, exclude_id=item.id):
            return False, '同级出监原因已存在', None

        old_level = item.level
        new_level = (parent.level + 1) if parent else 1
        ExitTypeRepository.update(
            item,
            type_name=type_name,
            parent=parent,
            level=new_level,
            sort_order=sort_order or 0,
            status=status or 'active',
        )
        if old_level != new_level:
            ExitTypeService._refresh_descendant_levels(item)

        logger.info(f"Exit type updated: id={item.id}, name={type_name}")
        return True, '更新成功', ExitTypeService._serialize(item)

    @staticmethod
    def delete_exit_type(exit_type_id):
        item = ExitTypeRepository.get_by_id(exit_type_id)
        if not item:
            return False, '出监原因不存在', None

        ExitTypeRepository.delete(item)
        logger.info(f"Exit type deleted: id={exit_type_id}")
        return True, '删除成功', None

    @staticmethod
    def _is_descendant(candidate_parent, item_id):
        current = candidate_parent
        while current:
            if current.parent_id == item_id:
                return True
            current = current.parent
        return False

    @staticmethod
    def _refresh_descendant_levels(item):
        for child in item.children.all():
            child.level = item.level + 1
            child.save(update_fields=['level', 'updated_at'])
            ExitTypeService._refresh_descendant_levels(child)
