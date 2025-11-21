from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='menu_items')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='menu_images/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f"{self.name} - ${self.price}"

class Table(models.Model):
    TABLE_SIZES = [
        (2, '2 persons'),
        (4, '4 persons'),
        (6, '6 persons'),
        (8, '8 persons'),
    ]
    
    number = models.IntegerField(unique=True)
    capacity = models.IntegerField(choices=TABLE_SIZES)
    location = models.CharField(max_length=50, blank=True)  # window, center, etc.
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['number']
    
    def __str__(self):
        return f"Table {self.number} ({self.capacity} persons)"

class Booking(models.Model):
    TIME_SLOTS = [
        ('17:00', '5:00 PM'),
        ('18:00', '6:00 PM'),
        ('19:00', '7:00 PM'),
        ('20:00', '8:00 PM'),
        ('21:00', '9:00 PM'),
        ('22:00', '10:00 PM'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()
    time_slot = models.CharField(max_length=5, choices=TIME_SLOTS)
    number_of_guests = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    special_requests = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-time_slot']
        unique_together = ['table', 'date', 'time_slot']
        indexes = [
            models.Index(fields=['date', 'time_slot']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"Booking #{self.id} - {self.customer_name} - {self.date} {self.time_slot}"
    
    def is_past_due(self):
        """Check if booking date is in the past"""
        from django.utils import timezone
        from datetime import datetime
        booking_datetime = datetime.combine(self.date, datetime.strptime(self.time_slot, '%H:%M').time())
        return booking_datetime < timezone.now()
    
    def save(self, *args, **kwargs):
        # Auto-update status for past bookings
        if self.is_past_due() and self.status not in ['cancelled', 'completed']:
            self.status = 'completed'
        super().save(*args, **kwargs)

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - ${self.total}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    
    class Meta:
        unique_together = ['order', 'menu_item']
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} - ${self.price}"
    
    def save(self, *args, **kwargs):
        self.unit_price = self.menu_item.price
        self.price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        
        # Update order total
        self.order.total = sum(item.price for item in self.order.items.all())
        self.order.save()