from django.contrib import admin
from .models import Category, MenuItem, Table, Booking, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'menu_items_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    
    def menu_items_count(self, obj):
        return obj.menu_items.count()
    menu_items_count.short_description = 'Menu Items'

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'is_available', 'created_at']
    list_filter = ['category', 'is_available', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'is_available']

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'capacity', 'location', 'is_available', 'created_at']
    list_filter = ['capacity', 'is_available', 'location']
    list_editable = ['is_available']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'date', 'time_slot', 'table', 'number_of_guests', 'status', 'created_at']
    list_filter = ['status', 'date', 'time_slot', 'created_at']
    search_fields = ['customer_name', 'customer_email', 'customer_phone']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'booking__customer_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'quantity', 'unit_price', 'price']
    list_filter = ['order__status']
    search_fields = ['order__id', 'menu_item__name']