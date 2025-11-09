from django.contrib import admin
from .models import RoomCategory, Room, RoomImage, GalleryImage, Booking

class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display=("number","category","price_per_night","capacity","is_active")
    list_filter=("category","is_active")
    inlines=[RoomImageInline]

admin.site.register(RoomCategory)
admin.site.register(GalleryImage)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display=("id","user","room","check_in_date","check_out_date","status","total_price")
    list_filter=("status","check_in_date")
    search_fields=("user__username","room__number")
