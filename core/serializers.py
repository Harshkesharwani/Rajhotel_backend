from rest_framework import serializers
from django.contrib.auth.models import User
from .models import RoomCategory, Room, RoomImage, GalleryImage, Booking

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username","first_name","last_name","email","is_staff"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ["username","email","password"]
    def create(self, v):
        return User.objects.create_user(**v)

class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ["id","image","caption"]

class RoomSerializer(serializers.ModelSerializer):
    images = RoomImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    class Meta:
        model = Room
        fields = ["id","number","category","category_name","price_per_night",
                  "capacity","description","is_active","images"]

class GalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryImage
        fields = ["id","image","caption","is_published"]

class BookingSerializer(serializers.ModelSerializer):
    room_detail = RoomSerializer(source="room", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    class Meta:
        model = Booking
        read_only_fields=("total_price","approved_by","declined_reason","status")
        fields = ["id","user","room","room_detail","check_in_date","check_out_date",
                  "guests","status","status_display","total_price","approved_by",
                  "declined_reason","created_at","updated_at"]
        extra_kwargs={"user":{"read_only":True}}

class BookingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["check_in_date","check_out_date","guests"]

class RoomCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomCategory
        fields = "__all__"