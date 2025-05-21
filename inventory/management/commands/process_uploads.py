from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from inventory.models import Stock, Sale, UploadedFile
import csv
import os
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = 'Process uploaded data files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file-id',
            type=int,
            help='ID of the uploaded file to process'
        )
        parser.add_argument(
            '--process-all',
            action='store_true',
            help='Process all pending uploaded files'
        )

    def handle(self, *args, **options):
        file_id = options.get('file_id')
        process_all = options.get('process_all')

        if file_id:
            try:
                uploaded_file = UploadedFile.objects.get(id=file_id)
                self.process_file(uploaded_file)
            except UploadedFile.DoesNotExist:
                raise CommandError(f'Uploaded file with ID {file_id} does not exist.')
        
        elif process_all:
            pending_files = UploadedFile.objects.filter(processing_status='pending')
            if not pending_files.exists():
                self.stdout.write('No pending files to process.')
                return
            
            for uploaded_file in pending_files:
                self.process_file(uploaded_file)
        
        else:
            raise CommandError('Please specify either --file-id or --process-all')

    def process_file(self, uploaded_file):
        """Process a single uploaded file"""
        self.stdout.write(f'Processing file: {uploaded_file.file_name}')
        
        # Update status to processing
        uploaded_file.processing_status = 'processing'
        uploaded_file.save()
        
        try:
            if uploaded_file.file_type == 'stock':
                records_processed = self.process_stock_file(uploaded_file)
            elif uploaded_file.file_type == 'sales':
                records_processed = self.process_sales_file(uploaded_file)
            else:
                raise ValueError(f'Unknown file type: {uploaded_file.file_type}')
            
            # Update success status
            uploaded_file.processing_status = 'completed'
            uploaded_file.records_processed = records_processed
            uploaded_file.error_message = None
            uploaded_file.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully processed {records_processed} records from {uploaded_file.file_name}')
            )
        
        except Exception as e:
            # Update error status
            uploaded_file.processing_status = 'failed'
            uploaded_file.error_message = str(e)
            uploaded_file.save()
            
            self.stdout.write(
                self.style.ERROR(f'Error processing {uploaded_file.file_name}: {e}')
            )

    def process_stock_file(self, uploaded_file):
        """Process stock data file"""
        records_processed = 0
        file_path = uploaded_file.file_path.path
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if not row.get('product_name'):
                    continue
                
                # Create or update stock
                stock_data = {
                    'quantity': int(row.get('quantity', 0)),
                    'price': Decimal(str(row.get('price', 0))),
                    'supplier': row.get('supplier', ''),
                    'category': row.get('category', ''),
                    'sku': row.get('sku', ''),
                    'description': row.get('description', ''),
                    'minimum_stock': int(row.get('minimum_stock', 0)),
                }
                
                stock, created = Stock.objects.get_or_create(
                    user=uploaded_file.user,
                    product_name=row['product_name'],
                    defaults=stock_data
                )
                
                if not created:
                    # Update existing stock
                    stock.quantity += int(row.get('quantity', 0))
                    stock.price = Decimal(str(row.get('price', stock.price)))
                    stock.supplier = row.get('supplier', stock.supplier)
                    stock.category = row.get('category', stock.category)
                    stock.sku = row.get('sku', stock.sku)
                    stock.description = row.get('description', stock.description)
                    stock.minimum_stock = int(row.get('minimum_stock', stock.minimum_stock))
                    stock.save()
                
                records_processed += 1
        
        return records_processed

    def process_sales_file(self, uploaded_file):
        """Process sales data file"""
        records_processed = 0
        file_path = uploaded_file.file_path.path
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if not row.get('product_name'):
                    continue
                
                # Find stock item
                try:
                    stock = Stock.objects.get(
                        user=uploaded_file.user,
                        product_name=row['product_name']
                    )
                except Stock.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Stock item "{row["product_name"]}" not found, skipping sale record')
                    )
                    continue
                
                # Parse date
                sale_date = datetime.now()
                if row.get('sale_date'):
                    try:
                        sale_date = datetime.strptime(row['sale_date'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            sale_date = datetime.strptime(row['sale_date'], '%Y-%m-%d')
                        except ValueError:
                            pass
                
                # Create sale
                quantity_sold = int(row.get('quantity_sold', 0))
                unit_price = Decimal(str(row.get('unit_price', stock.price)))
                
                # Check stock availability
                if stock.quantity < quantity_sold:
                    self.stdout.write(
                        self.style.WARNING(f'Insufficient stock for {stock.product_name}. Available: {stock.quantity}, Required: {quantity_sold}')
                    )
                    continue
                
                sale_data = {
                    'user': uploaded_file.user,
                    'product': stock,
                    'quantity_sold': quantity_sold,
                    'unit_price': unit_price,
                    'total_amount': quantity_sold * unit_price,
                    'customer_name': row.get('customer_name', ''),
                    'customer_phone': row.get('customer_phone', ''),
                    'customer_email': row.get('customer_email', ''),
                    'notes': row.get('notes', ''),
                    'sale_date': sale_date,
                }
                
                # Create sale (will automatically update stock)
                Sale.objects.create(**sale_data)
                records_processed += 1
        
        return records_processed