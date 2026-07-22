from rest_framework import serializers

class UpdateLocationRequestSerializer(serializers.Serializer):
    lat = serializers.FloatField(help_text="Latitude")
    lng = serializers.FloatField(help_text="Longitude")


class UpdateLocationResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    last_updated = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")


class LastKnownLocationResponseSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    last_updated = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")