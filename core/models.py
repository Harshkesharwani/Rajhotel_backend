from django.db import models
from django.conf import settings

class RoomCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

# class RoomCategory(Timestamped):
#     name = models.CharField(max_length=100, unique=True)
#     description = models.TextField(blank=True)
#     def __str__(self): return self.name

class Room(models.Model):
    number = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(RoomCategory, on_delete=models.CASCADE, related_name="rooms")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.IntegerField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.number}"

class RoomImage(Timestamped):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="rooms/")
    caption = models.CharField(max_length=255, blank=True)

class GalleryImage(Timestamped):
    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=255, blank=True)
    is_published = models.BooleanField(default=True)

class Booking(Timestamped):
    class Status(models.TextChoices):
        PENDING="PENDING","Pending"
        APPROVED="APPROVED","Approved"
        DECLINED="DECLINED","Declined"
        CHECKED_IN="CHECKED_IN","Checked In"
        CHECKED_OUT="CHECKED_OUT","Checked Out"
        CANCELLED="CANCELLED","Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="bookings")
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    guests = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="approved_bookings")
    declined_reason = models.TextField(blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.check_in_date >= self.check_out_date:
            raise ValidationError("check_out_date must be after check_in_date")
        if self.guests > self.room.capacity:
            raise ValidationError("guests exceed room capacity")
        overlapping = Booking.objects.exclude(id=self.id).filter(
            room=self.room,
            status__in=[self.Status.PENDING, self.Status.APPROVED, self.Status.CHECKED_IN],
            check_in_date__lt=self.check_out_date,
            check_out_date__gt=self.check_in_date,
        ).exists()
        if overlapping:
            raise ValidationError("Room not available for selected dates")

    def nights(self): return (self.check_out_date - self.check_in_date).days
    def compute_total(self): return self.nights() * self.room.price_per_night

    def save(self,*a,**kw):
        self.full_clean()
        self.total_price = self.compute_total()
        super().save(*a,**kw)

    def can_transition(self, to_status):
        allowed = {
            self.Status.PENDING:{self.Status.APPROVED,self.Status.DECLINED,self.Status.CANCELLED},
            self.Status.APPROVED:{self.Status.CHECKED_IN,self.Status.CANCELLED},
            self.Status.CHECKED_IN:{self.Status.CHECKED_OUT},
            self.Status.CHECKED_OUT:set(),
            self.Status.DECLINED:set(),
            self.Status.CANCELLED:set(),
        }
        return to_status in allowed.get(self.status,set())
