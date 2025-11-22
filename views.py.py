from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.shortcuts import get_object_or_404
from .models import Category, MenuItem, Table, Booking, Order, OrderItem
from .serializers import (
    UserSerializer, UserRegistrationSerializer, CategorySerializer,
    MenuItemSerializer, TableSerializer, BookingSerializer,
    OrderSerializer, OrderCreateSerializer, OrderItemSerializer
)
from django.contrib.auth.models import User

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'category__name']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]

class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['capacity', 'is_available', 'location']
    ordering_fields = ['number', 'capacity']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['date', 'status', 'table']
    search_fields = ['customer_name', 'customer_email', 'customer_phone']
    ordering_fields = ['date', 'time_slot', 'created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)
    
    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to cancel this booking.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status in ['cancelled', 'completed']:
            return Response(
                {'error': f'Cannot cancel a booking that is already {booking.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """Get available time slots for a specific date"""
        date_str = request.GET.get('date')
        guests = request.GET.get('guests', 2)
        
        if not date_str:
            return Response(
                {'error': 'Date parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            guests = int(guests)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date or guests parameter.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all time slots
        all_slots = [slot[0] for slot in Booking.TIME_SLOTS]
        
        # Get tables that can accommodate the number of guests
        suitable_tables = Table.objects.filter(
            capacity__gte=guests,
            is_available=True
        )
        
        # Find available slots
        available_slots = []
        for slot in all_slots:
            # Count how many suitable tables are available for this slot
            booked_tables_count = Booking.objects.filter(
                date=booking_date,
                time_slot=slot,
                status__in=['pending', 'confirmed']
            ).count()
            
            available_tables_count = suitable_tables.count() - booked_tables_count
            
            if available_tables_count > 0:
                available_slots.append({
                    'time_slot': slot,
                    'display_time': dict(Booking.TIME_SLOTS)[slot],
                    'available_tables': available_tables_count
                })
        
        return Response({
            'date': date_str,
            'guests': guests,
            'available_slots': available_slots
        })

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'booking']
    ordering_fields = ['created_at', 'total']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff members can update order status.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

# Authentication views
@api_view(['POST'])
@permission_classes([])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([])
def login(request):
    from django.contrib.auth import authenticate
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    
    return Response(
        {'error': 'Invalid credentials.'},
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out.'})
    except Exception as e:
        return Response(
            {'error': 'Error during logout.'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

# Dashboard and analytics
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def dashboard_stats(request):
    """Get dashboard statistics for admin"""
    
    # Bookings statistics
    total_bookings = Booking.objects.count()
    today_bookings = Booking.objects.filter(date=date.today()).count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    
    # Orders statistics
    total_orders = Order.objects.count()
    today_orders = Order.objects.filter(created_at__date=date.today()).count()
    pending_orders = Order.objects.filter(status='pending').count()
    
    # Revenue statistics
    total_revenue = Order.objects.aggregate(total=Sum('total'))['total'] or 0
    today_revenue = Order.objects.filter(
        created_at__date=date.today()
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Popular menu items
    popular_items = OrderItem.objects.values(
        'menu_item__name'
    ).annotate(
        total_ordered=Sum('quantity')
    ).order_by('-total_ordered')[:5]
    
    return Response({
        'bookings': {
            'total': total_bookings,
            'today': today_bookings,
            'pending': pending_bookings
        },
        'orders': {
            'total': total_orders,
            'today': today_orders,
            'pending': pending_orders
        },
        'revenue': {
            'total': float(total_revenue),
            'today': float(today_revenue)
        },
        'popular_items': list(popular_items)
    })