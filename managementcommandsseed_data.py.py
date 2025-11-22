from django.core.management.base import BaseCommand
from restaurant.models import Category, MenuItem, Table
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create sample data for Little Lemon restaurant'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create categories
        categories_data = [
            {'name': 'Appetizers', 'description': 'Start your meal with our delicious appetizers'},
            {'name': 'Main Courses', 'description': 'Hearty main dishes for every taste'},
            {'name': 'Desserts', 'description': 'Sweet endings to your perfect meal'},
            {'name': 'Beverages', 'description': 'Refreshing drinks and beverages'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create menu items
        menu_items_data = [
            {'name': 'Bruschetta', 'price': 8.99, 'category': 'Appetizers', 'description': 'Toasted bread topped with tomatoes and basil'},
            {'name': 'Calamari', 'price': 12.99, 'category': 'Appetizers', 'description': 'Crispy fried squid with marinara sauce'},
            {'name': 'Grilled Salmon', 'price': 24.99, 'category': 'Main Courses', 'description': 'Fresh salmon with lemon butter sauce'},
            {'name': 'Chicken Parmesan', 'price': 18.99, 'category': 'Main Courses', 'description': 'Breaded chicken with tomato sauce and cheese'},
            {'name': 'Tiramisu', 'price': 7.99, 'category': 'Desserts', 'description': 'Classic Italian coffee-flavored dessert'},
            {'name': 'Chocolate Lava Cake', 'price': 8.99, 'category': 'Desserts', 'description': 'Warm chocolate cake with molten center'},
            {'name': 'Italian Soda', 'price': 4.99, 'category': 'Beverages', 'description': 'Refreshing sparkling drink with fruit syrup'},
            {'name': 'House Wine', 'price': 9.99, 'category': 'Beverages', 'description': 'Glass of our finest house wine'},
        ]
        
        for item_data in menu_items_data:
            category = Category.objects.get(name=item_data['category'])
            menu_item, created = MenuItem.objects.get_or_create(
                name=item_data['name'],
                defaults={
                    'price': item_data['price'],
                    'category': category,
                    'description': item_data['description']
                }
            )
            if created:
                self.stdout.write(f'Created menu item: {menu_item.name}')
        
        # Create tables
        tables_data = [
            (1, 2, 'Window'),
            (2, 2, 'Window'),
            (3, 4, 'Center'),
            (4, 4, 'Center'),
            (5, 4, 'Center'),
            (6, 6, 'Private'),
            (7, 6, 'Private'),
            (8, 8, 'Private'),
            (9, 4, 'Patio'),
            (10, 4, 'Patio'),
        ]
        
        for number, capacity, location in tables_data:
            table, created = Table.objects.get_or_create(
                number=number,
                defaults={
                    'capacity': capacity,
                    'location': location
                }
            )
            if created:
                self.stdout.write(f'Created table: {table.number} ({capacity} persons)')
        
        # Create admin user if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@littlelemon.com', 'admin123')
            self.stdout.write('Created admin user: admin / admin123')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )