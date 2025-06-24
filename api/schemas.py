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

class TimeSeriesSerializer(serializers.Serializer):
    min_lon = serializers.FloatField(default=30.304434642130218, help_text="Minimum longitude")
    min_lat = serializers.FloatField(default=30.174682637534644, help_text="Minimum latitude")
    max_lon = serializers.FloatField(default=30.42143846734797, help_text="Maximum longitude")
    max_lat = serializers.FloatField(default=30.283438554006977, help_text="Maximum latitude")
    start_date = serializers.CharField(default="2025-01-01", help_text="Start date in YYYY-MM-DD format")
    end_date = serializers.CharField(default="2025-03-01", help_text="End date in YYYY-MM-DD format")
    cloud_cover = serializers.IntegerField(default=30, help_text="Maximum cloud cover percentage")
    band1 = serializers.CharField(default="red", help_text="First band for calculation")
    band2 = serializers.CharField(default="nir", help_text="Second band for calculation")
    formula = serializers.CharField(default="(band2-band1)/(band2+band1)", help_text="Formula for band calculation")
    operation = serializers.CharField(default="median", help_text="Statistical operation to apply")
    timeseries = serializers.BooleanField(default=True, help_text="Whether to compute time series")
    workers = serializers.IntegerField(default=16, help_text="Number of workers for processing")

time_series_schema = extend_schema(
    request=TimeSeriesSerializer,
    responses={
        200: OpenApiResponse(description="Time series computation completed successfully and files returned"),
        400: OpenApiResponse(description="VirtuGhan package not installed or computation failed"),
    },
    description="Compute time series using VirtuGhan Python package directly and return GIF and values file.",
)
