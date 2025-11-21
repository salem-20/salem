from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'menu-items', views.MenuItemViewSet)
router.register(r'tables', views.TableViewSet)
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.user_profile, name='profile'),
    
    # Additional endpoints
    path('bookings/available-slots/', views.BookingViewSet.as_view({'get': 'available_slots'}), name='available-slots'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
]