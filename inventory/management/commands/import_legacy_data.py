from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from inventory.models import Stock, Sale
import sqlite3
import os
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = 'Import data from the old SQLite database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--db-path',
            type=str,
            default='smc.db',
            help='Path to the old SQLite database file'
        )
        parser.add_argument(
            '--user',
            type=str,
            required=True,
            help='Username to assign the imported data to'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import'
        )

    def handle(self, *args, **options):
        db_path = options['db_path']
        username = options['user']
        clear_data = options['clear']

        # Check if database file exists
        if not os.path.exists(db_path):
            raise CommandError(f'Database file "{db_path}" does not exist.')

        # Get or create user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist. Please create the user first.')

        self.stdout.write(f'Importing data for user: {user.username}')

        # Clear existing data if requested
        if clear_data:
            self.stdout.write('Clearing existing data...')
            Stock.objects.filter(user=user).delete()
            Sale.objects.filter(user=user).delete()

        # Connect to old database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Import stock data
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock'")
            if cursor.fetchone():
                self.import_stock_data(cursor, user)
            else:
                self.stdout.write(self.style.WARNING('No stock table found in database'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing stock data: {e}'))

        # Import sales data
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales'")
            if cursor.fetchone():
                self.import_sales_data(cursor, user)
            else:
                self.stdout.write(self.style.WARNING('No sales table found in database'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing sales data: {e}'))

        conn.close()
        self.stdout.write(self.style.SUCCESS('Data import completed successfully!'))

    def import_stock_data(self, cursor, user):
        """Import stock data from old database"""
        self.stdout.write('Importing stock data...')
        
        # Get column names
        cursor.execute("PRAGMA table_info(stock)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Fetch all stock data
        cursor.execute("SELECT * FROM stock")
        rows = cursor.fetchall()
        
        stock_count = 0
        for row in rows:
            row_dict = dict(zip(columns, row))
            
            # Map old fields to new model fields
            stock_data = {
                'user': user,
                'product_name': row_dict.get('ProductName', row_dict.get('product_name', 'Unknown')),
                'quantity': int(row_dict.get('Quantity', row_dict.get('quantity', 0))),
                'price': Decimal(str(row_dict.get('Price', row_dict.get('price', 0)))),
                'supplier': row_dict.get('Supplier', row_dict.get('supplier', '')),
                'category': row_dict.get('Category', row_dict.get('category', '')),
                'sku': row_dict.get('SKU', row_dict.get('sku', '')),
                'description': row_dict.get('Description', row_dict.get('description', '')),
                'minimum_stock': int(row_dict.get('MinimumStock', row_dict.get('minimum_stock', 0))),
            }
            
            # Create or update stock
            stock, created = Stock.objects.get_or_create(
                user=user,
                product_name=stock_data['product_name'],
                defaults=stock_data
            )
            
            if not created:
                # Update existing stock
                for key, value in stock_data.items():
                    if key != 'user' and key != 'product_name':
                        setattr(stock, key, value)
                stock.save()
            
            stock_count += 1
        
        self.stdout.write(f'Imported {stock_count} stock items')

    def import_sales_data(self, cursor, user):
        """Import sales data from old database"""
        self.stdout.write('Importing sales data...')
        
        # Get column names
        cursor.execute("PRAGMA table_info(sales)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Fetch all sales data
        cursor.execute("SELECT * FROM sales")
        rows = cursor.fetchall()
        
        sales_count = 0
        for row in rows:
            row_dict = dict(zip(columns, row))
            
            # Find corresponding stock item
            product_name = row_dict.get('ProductName', row_dict.get('product_name', ''))
            try:
                stock = Stock.objects.get(user=user, product_name=product_name)
            except Stock.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Stock item "{product_name}" not found, skipping sale record'))
                continue
            
            # Parse date
            sale_date = row_dict.get('EntryDate', row_dict.get('sale_date', datetime.now()))
            if isinstance(sale_date, str):
                try:
                    sale_date = datetime.strptime(sale_date, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        sale_date = datetime.strptime(sale_date, '%Y-%m-%d')
                    except ValueError:
                        sale_date = datetime.now()
            
            # Create sale record
            quantity_sold = int(row_dict.get('QuantitySold', row_dict.get('quantity_sold', 0)))
            unit_price = Decimal(str(row_dict.get('UnitPrice', row_dict.get('unit_price', stock.price))))
            
            sale_data = {
                'user': user,
                'product': stock,
                'quantity_sold': quantity_sold,
                'unit_price': unit_price,
                'total_amount': quantity_sold * unit_price,
                'customer_name': row_dict.get('CustomerName', row_dict.get('customer_name', '')),
                'customer_phone': row_dict.get('CustomerPhone', row_dict.get('customer_phone', '')),
                'customer_email': row_dict.get('CustomerEmail', row_dict.get('customer_email', '')),
                'notes': row_dict.get('Notes', row_dict.get('notes', '')),
                'sale_date': sale_date,
            }
            
            # Create sale (don't auto-update stock since it's historical data)
            Sale.objects.create(**sale_data)
            sales_count += 1
        
        self.stdout.write(f'Imported {sales_count} sales records')