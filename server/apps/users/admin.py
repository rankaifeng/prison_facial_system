from django.contrib import admin
from .models import User, Device, DeviceSyncLog, FaceRecognitionRecord


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'role', 'role_name', 'prison_name']


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_no', 'name', 'prison_area', 'is_online', 'last_seen_at', 'remark']
    list_filter = ['is_online', 'prison_area']
    search_fields = ['device_no', 'name']
    readonly_fields = ['last_seen_at', 'client_id', 'created_at']


@admin.register(DeviceSyncLog)
class DeviceSyncLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'prisoner_no', 'sync_type', 'status', 'error_msg', 'synced_at']
    list_filter = ['status', 'sync_type', 'device']
    search_fields = ['prisoner_no', 'device__device_no']
    readonly_fields = ['synced_at']


@admin.register(FaceRecognitionRecord)
class FaceRecognitionRecordAdmin(admin.ModelAdmin):
    list_display = ['device_no', 'user_id', 'prisoner', 'recognized_at', 'created_at']
    list_filter = ['device_no', 'recognized_at']
    search_fields = ['user_id', 'device_no', 'prisoner__prisoner_no']
    readonly_fields = ['created_at', 'raw_data']
