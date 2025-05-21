## Sales & Inventory Management System - Django

A multi-user Sales & Inventory Management System built with Django, upgraded from Flask.

## Features

- **Multi-user Support**: Each user has their own isolated data
- **Stock Management**: Add, edit, track inventory with low stock alerts
- **Sales Tracking**: Record sales, customer information, and generate reports
- **File Upload**: Import stock and sales data from CSV/Excel files
- **User Authentication**: Registration, login, password management
- **Dashboard**: Real-time statistics and insights
- **PWA Support**: Progressive Web App capabilities
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tmp-smc
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Open http://127.0.0.1:8000/
   - Register a new account or login with superuser credentials

### Data Migration from Flask

If you have existing data from the Flask version:

```bash
# Import legacy data (requires old smc.db file)
python manage.py import_legacy_data --user your_username --db-path smc.db
```

## File Upload Format

### Stock Data CSV Format
```csv
product_name,quantity,price,supplier,category,sku,description,minimum_stock
"Widget A",100,10.50,"Supplier 1","Electronics","WID001","Electronic widget",10
```

## Management Commands

- `python manage.py import_legacy_data --user <username> --db-path <path>`: Import from old Flask database
- `python manage.py process_uploads --process-all`: Process pending uploaded files
- `python manage.py createsuperuser`: Create admin user

## Multi-User Features

- Each user has completely isolated data
- User registration with company information
- Individual dashboards and reports
- Secure data separation at the database level

## Features
- View Sales Transactions With Date Picker.
- View Sales Invoice Items.
- Check Stock For Products In Inventory.
- Sort Inventory Items With Stock Value.

## Tech
* Django
* PostgreSQL
* Celery, Redis
* REST-API
* Bootstrap
* Docker, nginx

## Screenshots
![N|Solid](https://i.ibb.co/bKdZ2Bx/Image.png)

![N|Solid](https://i.ibb.co/nzjvj61/Image.png)

![N|Solid](https://i.ibb.co/q0H8ML0/Image.png)
