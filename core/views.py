from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Room, RoomImage, GalleryImage, Booking, RoomCategory
from .serializers import (
    UserSerializer, RegisterSerializer,
    RoomSerializer, RoomImageSerializer, GalleryImageSerializer,
    BookingSerializer, BookingUpdateSerializer, RoomCategorySerializer,
)

# ---- Auth ----
class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["is_staff"] = user.is_staff
        return token

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class RegisterViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class MeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):  # GET /auth/me/
        return Response(UserSerializer(request.user).data)

class RoomCategoryViewSet(viewsets.ModelViewSet):
    queryset = RoomCategory.objects.all()
    serializer_class = RoomCategorySerializer
    permission_classes = [IsAdminUser]

    class Meta:
        model = RoomCategory
        fields = '__all__'


# ---- Rooms ----
class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related("category").prefetch_related("images").all()
    serializer_class = RoomSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["category","capacity","is_active"]
    search_fields = ["number","description","category__name"]

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def images(self, request, pk=None):
        room = self.get_object()
        ser = RoomImageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(room=room)
        return Response(ser.data, status=201)

# ---- Gallery ----
class GalleryViewSet(viewsets.ModelViewSet):
    queryset = GalleryImage.objects.all()
    serializer_class = GalleryImageSerializer
    permission_classes = [IsAdminUser]  # publish by admin
    def get_permissions(self):
        if self.action in ["list","retrieve"]:
            return [AllowAny()]
        return super().get_permissions()

# ---- Bookings ----
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related("room","user").all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ["update","partial_update"]:
            return BookingUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        qs = self.queryset.filter(user=request.user)
        return Response(BookingSerializer(qs, many=True).data)

    # -- Admin decisions --
    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        b = self.get_object()
        if not b.can_transition(Booking.Status.APPROVED):
            return Response({"detail":"Cannot approve from current status."}, status=400)
        b.status = Booking.Status.APPROVED; b.approved_by=request.user; b.declined_reason=""
        b.save(); return Response(BookingSerializer(b).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def decline(self, request, pk=None):
        b = self.get_object()
        if not b.can_transition(Booking.Status.DECLINED):
            return Response({"detail":"Cannot decline from current status."}, status=400)
        b.status = Booking.Status.DECLINED; b.approved_by=None; b.declined_reason=request.data.get("reason","")
        b.save(); return Response(BookingSerializer(b).data)

    # -- Lifecycle --
    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def check_in(self, request, pk=None):
        b = self.get_object()
        if not b.can_transition(Booking.Status.CHECKED_IN):
            return Response({"detail":"Cannot check-in from current status."}, status=400)
        b.status = Booking.Status.CHECKED_IN; b.save(); return Response(BookingSerializer(b).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def check_out(self, request, pk=None):
        b = self.get_object()
        if not b.can_transition(Booking.Status.CHECKED_OUT):
            return Response({"detail":"Cannot check-out from current status."}, status=400)
        b.status = Booking.Status.CHECKED_OUT; b.save(); return Response(BookingSerializer(b).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        b = self.get_object()
        if not b.can_transition(Booking.Status.CANCELLED):
            return Response({"detail":"Cannot cancel from current status."}, status=400)
        # allow owner or admin
        if not (request.user.is_staff or request.user.id == b.user_id):
            return Response({"detail":"Not allowed."}, status=403)
        b.status = Booking.Status.CANCELLED; b.save(); return Response(BookingSerializer(b).data)
