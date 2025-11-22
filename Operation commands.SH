# 1. Install requirements
pip install -r requirements.txt

# 2. Create migrations
python manage.py makemigrations

# 3. Apply migrations
python manage.py migrate

# 4. Create seed data
python manage.py seed_data

# 5. Run server
python manage.py runserver