from django.db import models
from django.db.models import JSONField

# Create your models here.
class Land(models.Model):
    address = models.TextField(blank=True, null=True)
    langitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    farm_name = models.CharField(max_length=256, blank=True, null=True)
    farm_size = models.FloatField(blank=True, null=True)
    land_user = models.ForeignKey("account.Profile", on_delete=models.CASCADE)
    class Meta:
        db_table = 'land'
    def __str__(self):
        return self.address

def get_upload_path(instance, filename):
    return f'farm_documents/{instance.user.id}/{instance.id}/{filename}'

class FarmArea(models.Model):
    name = models.CharField(max_length=255, help_text='Name of the specific area')
    # Area coordinates as array of [lat, long] points
    area_coordinates = JSONField(
        help_text='Array of [latitude, longitude] points that form the area boundary',
        null=True,
        blank=True,
        default=list
    )
    center_coordinates = JSONField(
        help_text='Center point [latitude, longitude] of the area',
        null=True,
        blank=True
    )
    
    primaryCrop = models.CharField(max_length=255, blank=True, null=True, help_text='Primary crop(s) grown')
    secondaryCrops = models.CharField(max_length=255, blank=True, null=True, help_text='Secondary crop(s) grown')
    soilType = models.CharField(max_length=255, blank=True, null=True, help_text='Type of soil (Clay, Sandy, Loam, etc.)')
    irrigationSystem = models.CharField(max_length=255, blank=True, null=True, help_text='Irrigation method(s) used')
    fertilizers = models.CharField(max_length=255, blank=True, null=True, help_text='Types of fertilizers used')
    fertilizationFrequency = models.CharField(max_length=255, blank=True, null=True, help_text='How often fertilizers are applied')
    fertilizationMethod = models.CharField(max_length=255, blank=True, null=True, help_text='Method of fertilizer application')
    commonPests = models.CharField(max_length=255, blank=True, null=True, help_text='Common pests and diseases')
    pesticides = models.CharField(max_length=255, blank=True, null=True, help_text='Pesticides/fungicides used')
    previousYield = models.CharField(max_length=255, blank=True, null=True, help_text="Previous season's yield data")
    soilTestResults = models.CharField(max_length=500, blank=True, null=True, help_text='Recent soil test results')
    yieldLosses = models.TextField(blank=True, null=True, help_text='Information about recent yield losses')
    additionalNotes = models.TextField(blank=True, null=True, help_text='Additional observations or comments')
    
    # File fields
    soilReports = models.FileField(upload_to=get_upload_path, null=True, blank=True)
    yieldData = models.FileField(upload_to=get_upload_path, null=True, blank=True)
    cropPhotos = models.FileField(upload_to=get_upload_path, null=True, blank=True)
    otherDocuments = models.FileField(upload_to=get_upload_path, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey("account.Profile", on_delete=models.CASCADE, related_name='farm_areas')

    class Meta:
        db_table = 'farm_areas'
        ordering = ['-created_at']
        verbose_name = 'Farm Area'
        verbose_name_plural = 'Farm Areas'

    def __str__(self):
        return f"{self.name} - {self.user.user.username}"
