from django.urls import path, include # Add include
from rest_framework.routers import DefaultRouter # Add DefaultRouter
from account.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

router = DefaultRouter()

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('profile/<int:user_id>/', views.ProfileView.as_view(), name='profile-detail'),
    path('lands/', views.LandView.as_view(), name='land-list'),
    path('logout/', views.LogOutAPIView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/<uuid:token>/', views.EmailVerificationView.as_view(), name='verify-email'),
    path('generate-tiles/', views.TileGenerationView.as_view(), name='generate-tiles'),
    path('tile-map/', views.TileMapView.as_view(), name='tile-map'),
    path('farm-areas/', views.FarmAreaView.as_view(), name='farm-area-list'),
    path('farm-areas/<int:pk>/', views.FarmAreaDetailView.as_view(), name='farm-area-detail'),
    path('time_series/', views.TimeSeriesView.as_view(), name='time_series'),
]