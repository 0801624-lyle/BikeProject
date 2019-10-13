from rest_framework import serializers

from .models import Location, Bikes

class BikeSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = Bikes
        fields = ("id", "status", "location")

    # def get_status(self, obj):
    #     return obj.get_status_display()

class LocationSerializer(serializers.ModelSerializer):
    bikes_set = BikeSerializer(many=True, read_only=True)

    class Meta:
        model = Location
        fields = ("station_name", "latitude", "longitude", 'bikes_set')