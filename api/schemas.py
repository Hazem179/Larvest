from drf_spectacular.utils import extend_schema,OpenApiResponse
from account.serializers import RegisterSerializer,LandSerializer
from rest_framework import serializers


register_schema = extend_schema(
        request=RegisterSerializer,
        responses={
            201: RegisterSerializer,
        },
        description="Register a new user account",
        
    )

land_schema = extend_schema(
        request=LandSerializer,
        responses={
            201: LandSerializer,
        },
        description="Add a new land for the user",
    )

class TileGenerationSerializer(serializers.Serializer):
    min_lon = serializers.FloatField(default=30.304434642130218)
    min_lat = serializers.FloatField(default=30.174682637534644)
    max_lon = serializers.FloatField(default=30.42143846734797)
    max_lat = serializers.FloatField(default=30.283438554006977)
    zoom_level = serializers.IntegerField(default=12)
    start_date = serializers.CharField(default="2025-01-01")
    end_date = serializers.CharField(default="2025-03-01")
    cloud_cover = serializers.IntegerField(default=30)
    band1 = serializers.CharField(default="red")
    band2 = serializers.CharField(default="nir")
    formula = serializers.CharField(default="(band2-band1)/(band2+band1)")
    colormap_str = serializers.CharField(default="RdYlGn")

tile_generation_schema = extend_schema(
    request=TileGenerationSerializer,
    responses={
        200: OpenApiResponse(description="Tile generation started successfully"),
    },
    description="Generate satellite image tiles for a specified bounding box",
)
