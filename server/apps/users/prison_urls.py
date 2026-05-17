from django.urls import re_path
from .controllers import (
    ExitTypeListController,
    ExitTypeAddController,
    ExitTypeUpdateController,
    ExitTypeDeleteController,
)

urlpatterns = [
    re_path(r'^exit_type/exit_type_list/?$', ExitTypeListController.as_view(), name='exit_type_list'),
    re_path(r'^exit_type/exit_type_add/?$', ExitTypeAddController.as_view(), name='exit_type_add'),
    re_path(r'^exit_type/exit_type_update/?$', ExitTypeUpdateController.as_view(), name='exit_type_update'),
    re_path(r'^exit_type/exit_type_delete/?$', ExitTypeDeleteController.as_view(), name='exit_type_delete'),
]
