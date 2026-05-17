from rest_framework import serializers


class ExitRecordSerializer(serializers.Serializer):
    prisoner_no = serializers.CharField(max_length=32, required=True)
    prisoner_name = serializers.CharField(max_length=64, required=True)
    prisoner_photo = serializers.CharField(max_length=255, required=False, allow_blank=True)
    prison_area = serializers.CharField(max_length=32, required=True)
    prison_area_name = serializers.CharField(max_length=128, required=True)
    exit_date = serializers.DateField(required=True)
    reason = serializers.ChoiceField(choices=[
        ('刑满释放', '刑满释放'),
        ('外出就医', '外出就医'),
        ('外出教育', '外出教育'),
        ('离监探亲', '离监探亲'),
        ('押回重审', '押回重审'),
    ], required=True)
    police_face = serializers.CharField(max_length=65535, required=True)
    swat_face = serializers.CharField(max_length=65535, required=True)
    armed_police_signature = serializers.CharField(max_length=65535, required=True)


class EntryRecordSerializer(serializers.Serializer):
    prisoner_no = serializers.CharField(max_length=32, required=True)
    prisoner_name = serializers.CharField(max_length=64, required=True)
    prisoner_photo = serializers.CharField(max_length=255, required=False, allow_blank=True)
    prison_area = serializers.CharField(max_length=32, required=True)
    prison_area_name = serializers.CharField(max_length=128, required=True)
    entry_date = serializers.DateField(required=True)
    police_face = serializers.CharField(max_length=65535, required=True)