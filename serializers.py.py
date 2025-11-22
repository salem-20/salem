from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Category, MenuItem, Table, Booking, Order, OrderItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['is_staff']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class CategorySerializer(serializers.ModelSerializer):
    menu_items_count = serializers.IntegerField(source='menu_items.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'menu_items_count', 'created_at']

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'price', 'category', 'category_name', 'description',
            'image', 'is_available', 'created_at', 'updated_at'
        ]

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'number', 'capacity', 'location', 'is_available', 'created_at']

class BookingSerializer(serializers.ModelSerializer):
    table_number = serializers.IntegerField(source='table.number', read_only=True)
    table_capacity = serializers.IntegerField(source='table.capacity', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    is_past_due = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'user_name', 'table', 'table_number', 'table_capacity',
            'date', 'time_slot', 'number_of_guests', 'customer_name',
            'customer_email', 'customer_phone', 'special_requests', 'status',
            'is_past_due', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'status', 'is_past_due']
    
    def validate(self, data):
        # Check if table is available for the selected date and time
        if self.instance is None:  # Only for create, not update
            table = data['table']
            date = data['date']
            time_slot = data['time_slot']
            
            conflicting_booking = Booking.objects.filter(
                table=table,
                date=date,
                time_slot=time_slot,
                status__in=['pending', 'confirmed']
            ).exists()
            
            if conflicting_booking:
                raise serializers.ValidationError(
                    "This table is already booked for the selected date and time."
                )
        
        # Check if number of guests exceeds table capacity
        if data['number_of_guests'] > data['table'].capacity:
            raise serializers.ValidationError(
                f"Number of guests exceeds table capacity. Maximum is {data['table'].capacity}."
            )
        
        return data

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_price = serializers.DecimalField(source='menu_item.price', read_only=True, max_digits=6, decimal_places=2)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'menu_item_name', 'menu_item_price',
            'quantity', 'unit_price', 'price'
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    booking_info = serializers.CharField(source='booking.__str__', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_name', 'booking', 'booking_info', 'status',
            'total', 'special_instructions', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'total']

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ['booking', 'special_instructions', 'items']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        return order