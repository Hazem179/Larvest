from rest_framework import serializers
from .models import FarmArea
from account.models import Profile

class FarmAreaSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all(), required=False)
    area_coordinates = serializers.JSONField(required=False)
    center_coordinates = serializers.JSONField(required=False)
    
    def validate_area_coordinates(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Area coordinates must be an array of points")
        
        for point in value:
            if not isinstance(point, list) or len(point) != 2:
                raise serializers.ValidationError("Each point must be an array of [latitude, longitude]")
            try:
                lat, lng = float(point[0]), float(point[1])
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    raise serializers.ValidationError("Invalid latitude or longitude values")
            except (ValueError, TypeError):
                raise serializers.ValidationError("Coordinates must be valid numbers")
        
        return value

    def validate_center_coordinates(self, value):
        if not isinstance(value, list) or len(value) != 2:
            raise serializers.ValidationError("Center coordinates must be an array of [latitude, longitude]")
        try:
            lat, lng = float(value[0]), float(value[1])
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                raise serializers.ValidationError("Invalid latitude or longitude values")
        except (ValueError, TypeError):
            raise serializers.ValidationError("Coordinates must be valid numbers")
        return value
    
    class Meta:
        model = FarmArea
        fields = [
            'id', 'name', 'area_coordinates', 'center_coordinates',
            'primaryCrop', 'secondaryCrops', 'soilType',
            'irrigationSystem', 'fertilizers', 'fertilizationFrequency',
            'fertilizationMethod', 'commonPests', 'pesticides',
            'previousYield', 'soilTestResults', 'yieldLosses',
            'additionalNotes', 'soilReports', 'yieldData', 'cropPhotos',
            'otherDocuments', 'created_at', 'updated_at', 'user'
        ]
        read_only_fields = ['created_at', 'updated_at']
