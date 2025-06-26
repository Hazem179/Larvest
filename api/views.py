import os
import asyncio
import tempfile
import json
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample
from account.models import Profile,Account
from account.serializers import ProfileSerializer,RegisterSerializer,LandSerializer
from .utils import generate_tiles_and_map
from .schemas import register_schema,land_schema, tile_generation_schema, TileGenerationSerializer, time_series_schema, TimeSeriesSerializer
from .models import Land, FarmArea
from .serializers import FarmAreaSerializer
from django.shortcuts import get_object_or_404 # For fetching objects or 404
from rest_framework import viewsets # Add viewsets import
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import glob
import uuid

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(responses=ProfileSerializer)
    def get(self, request, user_id=None):
        if user_id:
            try:
                profile = Profile.objects.get(user__id=user_id)
                serializer = ProfileSerializer(profile)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Profile.DoesNotExist:
                return Response(
                    {"detail": "Profile not found."}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            profiles = Profile.objects.all()
            serializer = ProfileSerializer(profiles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=ProfileSerializer,
        examples=[
            OpenApiExample(
                'Update Profile Example',
                value={
                    "user": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "username": "johndoe123",
                        "email": "john.doe@example.com"
                    },
                    "birth_date": "1990-01-01"
                },
                request_only=True,
                response_only=False,
            )
        ]
    )
    def put(self, request, user_id=None):
        if user_id:
            try:
                profile = Profile.objects.get(user__id=user_id)
            except Profile.DoesNotExist:
                return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                profile = Profile.objects.get(user=request.user)
            except Profile.DoesNotExist:
                return Response({"detail": "Profile not found for current user."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogOutAPIView(APIView):
    def post(self , request,format=None):
        response = Response("user logged out successfully")
        response.set_cookie('refresh_token' , '', expires=0)
        response.set_cookie('access_token' , '', expires=0)
        return response


class RegisterView(APIView):
    @register_schema
    def post(self,request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            forbidden_usernames = ['admin','root','superuser']
            if username in forbidden_usernames:
                return Response({"error":"Username is not allowed."},status=status.HTTP_400_BAD_REQUEST)
            user = serializer.save()
            response_data = serializer.data
            response_data['id'] = user.id
            return Response(response_data, status=status.HTTP_201_CREATED)
        errors = serializer.errors
        if "username" in errors and "non_field_errors" not in errors:
            return Response({"error":"Username already exists."},status=status.HTTP_400_BAD_REQUEST)
        return Response(errors,status=status.HTTP_400_BAD_REQUEST)
    
class EmailVerificationView(APIView):
    def get(self, request, token):
        try:
            user = Account.objects.get(verification_token=token)
            if not user.is_verified:
                user.is_verified = True
                user.save()
                return Response(
                    {'message': 'Email verified successfully.'},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'message': 'Email already verified.'},
                status=status.HTTP_200_OK
            )
        except Account.DoesNotExist:
            return Response(
                {'error': 'Invalid verification token.'},
                status=status.HTTP_404_NOT_FOUND
            )


class LandView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(responses=LandSerializer)
    def get(self, request,user_id):
        lands = Land.objects.filter(land_user=user_id)
        serializer = LandSerializer(lands, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @land_schema
    def post(self, request):
        try:
            land_user = Profile.objects.get(user_id=request.data.get('land_user'))
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found for the specified user ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        data = request.data.copy()
        data.pop('land_user', None)
        serializer = LandSerializer(data=data)
        if serializer.is_valid():
            land = serializer.save(land_user=land_user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TileGenerationView(APIView):
    # permission_classes = [IsAuthenticated]
    @tile_generation_schema
    def post(self, request):
        serializer = TileGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results, map_path, map_html = loop.run_until_complete(generate_tiles_and_map(**serializer.validated_data))
            loop.close()
            return Response(
                {
                    "message": "Tile generation and map creation completed successfully",
                    "tiles_generated": len(results) if results else 0,
                    "results": results,
                    "map_url": f"/api/tile-map/?path={os.path.basename(map_path)}" if map_path else None,
                    "map_html": map_html
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to generate tiles and map: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class TileMapView(APIView):
    def get(self, request):
        map_filename = request.GET.get('path')
        if not map_filename:
            return Response(
                {"error": "No map file specified"},
                status=status.HTTP_400_BAD_REQUEST
            )
        map_path = os.path.join(tempfile.gettempdir(), map_filename)
        if not os.path.exists(map_path):
            return Response(
                {"error": "Map file not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return FileResponse(
            open(map_path, 'rb'),
            content_type='text/html'
        )

class FarmAreaView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        responses={200: FarmAreaSerializer(many=True)},
        description="Get all farm areas for the authenticated user"
    )
    def get(self, request):
        farm_areas = FarmArea.objects.filter(user=Profile.objects.get(user=request.user))
        serializer = FarmAreaSerializer(farm_areas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=FarmAreaSerializer,
        responses={201: FarmAreaSerializer},
        description="Create a new farm area with coordinates"
    )
    def post(self, request):
        try:
            farm_area_data = request.data.copy()
            farm_area_data['user'] = Profile.objects.get(user=request.user).id
            
            # Handle area coordinates if provided
            if 'area_coordinates' in request.data:
                try:
                    # Parse coordinates if they're sent as a string
                    if isinstance(request.data['area_coordinates'], str):
                        coordinates = json.loads(request.data['area_coordinates'])
                    else:
                        coordinates = request.data['area_coordinates']
                    
                    # Validate coordinates format
                    if not isinstance(coordinates, list):
                        return Response(
                            {"error": "Area coordinates must be an array of points"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Validate each point
                    for point in coordinates:
                        if not isinstance(point, list) or len(point) != 2:
                            return Response(
                                {"error": "Each point must be an array of [latitude, longitude]"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        try:
                            lat, lng = float(point[0]), float(point[1])
                            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                                return Response(
                                    {"error": "Invalid latitude or longitude values"},
                                    status=status.HTTP_400_BAD_REQUEST
                                )
                        except (ValueError, TypeError):
                            return Response(
                                {"error": "Coordinates must be valid numbers"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    
                    farm_area_data['area_coordinates'] = coordinates
                except json.JSONDecodeError:
                    return Response(
                        {"error": "Invalid JSON format for area coordinates"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Handle center coordinates if provided
            if 'center_coordinates' in request.data:
                try:
                    # Parse coordinates if they're sent as a string
                    if isinstance(request.data['center_coordinates'], str):
                        center = json.loads(request.data['center_coordinates'])
                    else:
                        center = request.data['center_coordinates']
                    
                    # Validate center coordinates format
                    if not isinstance(center, list) or len(center) != 2:
                        return Response(
                            {"error": "Center coordinates must be an array of [latitude, longitude]"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    try:
                        lat, lng = float(center[0]), float(center[1])
                        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                            return Response(
                                {"error": "Invalid latitude or longitude values"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    except (ValueError, TypeError):
                        return Response(
                            {"error": "Coordinates must be valid numbers"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    farm_area_data['center_coordinates'] = center
                except json.JSONDecodeError:
                    return Response(
                        {"error": "Invalid JSON format for center coordinates"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            serializer = FarmAreaSerializer(data=farm_area_data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            farm_area = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class FarmAreaDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk):
        try:
            return FarmArea.objects.get(pk=pk, user=Profile.objects.get(user=self.request.user))
        except FarmArea.DoesNotExist:
            raise Http404

    @extend_schema(
        responses={200: FarmAreaSerializer},
        description="Get a specific farm area with coordinates"
    )
    def get(self, request, pk):
        farm_area = self.get_object(pk)
        serializer = FarmAreaSerializer(farm_area)
        return Response(serializer.data)

    @extend_schema(
        request=FarmAreaSerializer,
        responses={200: FarmAreaSerializer},
        description="Update a farm area with coordinates"
    )
    def put(self, request, pk):
        farm_area = self.get_object(pk)
        farm_area_data = request.data.copy()
        
        # Handle area coordinates if provided
        if 'area_coordinates' in request.data:
            try:
                # Parse coordinates if they're sent as a string
                if isinstance(request.data['area_coordinates'], str):
                    coordinates = json.loads(request.data['area_coordinates'])
                else:
                    coordinates = request.data['area_coordinates']
                
                # Validate coordinates format
                if not isinstance(coordinates, list):
                    return Response(
                        {"error": "Area coordinates must be an array of points"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate each point
                for point in coordinates:
                    if not isinstance(point, list) or len(point) != 2:
                        return Response(
                            {"error": "Each point must be an array of [latitude, longitude]"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    try:
                        lat, lng = float(point[0]), float(point[1])
                        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                            return Response(
                                {"error": "Invalid latitude or longitude values"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    except (ValueError, TypeError):
                        return Response(
                            {"error": "Coordinates must be valid numbers"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                farm_area_data['area_coordinates'] = coordinates
            except json.JSONDecodeError:
                return Response(
                    {"error": "Invalid JSON format for area coordinates"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Handle center coordinates if provided
        if 'center_coordinates' in request.data:
            try:
                # Parse coordinates if they're sent as a string
                if isinstance(request.data['center_coordinates'], str):
                    center = json.loads(request.data['center_coordinates'])
                else:
                    center = request.data['center_coordinates']
                
                # Validate center coordinates format
                if not isinstance(center, list) or len(center) != 2:
                    return Response(
                        {"error": "Center coordinates must be an array of [latitude, longitude]"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                try:
                    lat, lng = float(center[0]), float(center[1])
                    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                        return Response(
                            {"error": "Invalid latitude or longitude values"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except (ValueError, TypeError):
                    return Response(
                        {"error": "Coordinates must be valid numbers"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                farm_area_data['center_coordinates'] = center
            except json.JSONDecodeError:
                return Response(
                    {"error": "Invalid JSON format for center coordinates"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = FarmAreaSerializer(farm_area, data=farm_area_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={204: None},
        description="Delete a farm area"
    )
    def delete(self, request, pk):
        farm_area = self.get_object(pk)
        farm_area.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TimeSeriesView(APIView):
    """
    Compute time series using VirtuGhan Python package directly and return GIF and values file.
    """
    @time_series_schema
    def post(self, request):
        serializer = TimeSeriesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            from vcube.engine import VCubeProcessor
            import mercantile
            payload = serializer.validated_data
            # Create a unique output directory for this request
            unique_id = str(uuid.uuid4())
            base_output_dir = os.path.abspath("media/virtughan_output")
            output_dir = os.path.join(base_output_dir, unique_id)
            os.makedirs(output_dir, exist_ok=True)
            processor = VCubeProcessor(
                bbox=[payload["min_lon"], payload["min_lat"], payload["max_lon"], payload["max_lat"]],
                start_date=payload["start_date"],
                end_date=payload["end_date"],
                cloud_cover=payload["cloud_cover"],
                formula=payload["formula"],
                band1=payload["band1"],
                band2=payload["band2"],
                operation=payload["operation"],
                timeseries=payload["timeseries"],
                output_dir=output_dir,
                workers=payload["workers"]
            )
            result = processor.compute()
            # Find GIF and values file
            gif_file = None
            values_file = None
            gif_filename = None
            values_filename = None
            for f in os.listdir(output_dir):
                if f.endswith('.gif'):
                    gif_file = os.path.abspath(os.path.join(output_dir, f))
                    gif_filename = f
                elif f.startswith('values_over_time'):
                    values_file = os.path.abspath(os.path.join(output_dir, f))
                    values_filename = f
            # Delete all other files in output_dir
            for f in os.listdir(output_dir):
                full_path = os.path.abspath(os.path.join(output_dir, f))
                if full_path != gif_file and full_path != values_file:
                    os.remove(full_path)
            if not gif_file or not values_file:
                return Response({"error": "Required output files not found."}, status=status.HTTP_400_BAD_REQUEST)
            # Return media paths instead of full paths
            gif_media_path = f"media/virtughan_output/{unique_id}/{gif_filename}"
            values_media_path = f"media/virtughan_output/{unique_id}/{values_filename}"
            return Response(
                {
                    "message": "Time series computation completed successfully!",
                    "gif_file_path": gif_media_path,
                    "values_file_path": values_media_path,
                    "output_dir": f"media/virtughan_output/{unique_id}",
                    "request_id": unique_id
                },
                status=status.HTTP_200_OK
            )
        except ImportError:
            return Response(
                {
                    "error": "VirtuGhan package not installed. Install with: pip install VirtuGhan",
                    "detail": "The VirtuGhan package is required for this endpoint to work."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "error": f"VirtuGhan computation failed: {str(e)}",
                    "detail": "An error occurred during the time series computation."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

