from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, F
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json
import csv
from io import TextIOWrapper

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

from .models import Stock, Sale, UploadedFile, UserProfile
from .forms import (CustomUserCreationForm, StockForm, SaleForm, 
                   FileUploadForm, StockQueryForm)


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    """Main dashboard view"""
    user = request.user
    
    # Get dashboard statistics
    total_products = Stock.objects.filter(user=user).count()
    low_stock_count = Stock.objects.filter(user=user, quantity__lte=F('minimum_stock')).count()
    
    # Recent sales (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_sales = Sale.objects.filter(user=user, sale_date__gte=thirty_days_ago)
    total_sales = recent_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    sales_count = recent_sales.count()
    
    # Top selling products
    top_products = (Sale.objects.filter(user=user, sale_date__gte=thirty_days_ago)
                   .values('product__product_name')
                   .annotate(total_sold=Sum('quantity_sold'))
                   .order_by('-total_sold')[:5])
    
    # Low stock products
    low_stock_products = Stock.objects.filter(
        user=user, 
        quantity__lte=F('minimum_stock')
    ).order_by('quantity')[:10]
    
    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'total_sales': total_sales,
        'sales_count': sales_count,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
    }
    
    return render(request, 'inventory/dashboard.html', context)


@login_required
def stock_list(request):
    """Stock listing with search and pagination"""
    query = request.GET.get('q', '')
    stocks = Stock.objects.filter(user=request.user)
    
    if query:
        stocks = stocks.filter(
            Q(product_name__icontains=query) |
            Q(sku__icontains=query) |
            Q(supplier__icontains=query) |
            Q(category__icontains=query)
        )
    
    paginator = Paginator(stocks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'form': StockQueryForm(initial={'query': query})
    }
    
    return render(request, 'inventory/stock_list.html', context)


@login_required
def stock_query(request):
    """AJAX stock query for the original functionality"""
    query = request.GET.get('query', '')
    
    if query:
        stocks = Stock.objects.filter(
            user=request.user
        ).filter(
            Q(product_name__icontains=query) |
            Q(sku__icontains=query) |
            Q(supplier__icontains=query)
        )[:10]  # Limit results
        
        results = []
        for stock in stocks:
            results.append({
                'id': stock.id,
                'product_name': stock.product_name,
                'quantity': stock.quantity,
                'price': float(stock.price),
                'supplier': stock.supplier or '',
                'sku': stock.sku or '',
                'category': stock.category or '',
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})


@login_required
def add_stock(request):
    """Add new stock item"""
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            stock = form.save(commit=False)
            stock.user = request.user
            stock.save()
            messages.success(request, f'Stock item "{stock.product_name}" added successfully!')
            return redirect('stock_list')
    else:
        form = StockForm()
    
    return render(request, 'inventory/add_stock.html', {'form': form})


@login_required
def edit_stock(request, stock_id):
    """Edit existing stock item"""
    stock = get_object_or_404(Stock, id=stock_id, user=request.user)
    
    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request, f'Stock item "{stock.product_name}" updated successfully!')
            return redirect('stock_list')
    else:
        form = StockForm(instance=stock)
    
    return render(request, 'inventory/edit_stock.html', {'form': form, 'stock': stock})


@login_required
def sales_list(request):
    """Sales listing with pagination"""
    sales = Sale.objects.filter(user=request.user)
    
    # Date filtering
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        sales = sales.filter(sale_date__gte=date_from)
    if date_to:
        sales = sales.filter(sale_date__lte=date_to)
    
    paginator = Paginator(sales, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'inventory/sales_list.html', context)


@login_required
def add_sale(request):
    """Add new sale"""
    if request.method == 'POST':
        form = SaleForm(user=request.user, data=request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.user = request.user
            
            # Check if enough stock is available
            if sale.product.quantity < sale.quantity_sold:
                messages.error(request, f'Not enough stock available. Current stock: {sale.product.quantity}')
                return render(request, 'inventory/add_sale.html', {'form': form})
            
            sale.save()
            messages.success(request, f'Sale recorded successfully!')
            return redirect('sales_list')
    else:
        form = SaleForm(user=request.user)
    
    return render(request, 'inventory/add_sale.html', {'form': form})


@login_required
def upload_file(request):
    """File upload functionality"""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = UploadedFile.objects.create(
                user=request.user,
                file_name=request.FILES['file'].name,
                file_path=request.FILES['file'],
                file_type=form.cleaned_data['file_type'],
                processing_status='pending'
            )
            
            # Process the file
            try:
                records_processed = process_uploaded_file(uploaded_file)
                uploaded_file.records_processed = records_processed
                uploaded_file.processing_status = 'completed'
                uploaded_file.save()
                
                messages.success(request, f'File uploaded and {records_processed} records processed successfully!')
                
            except Exception as e:
                uploaded_file.processing_status = 'failed'
                uploaded_file.error_message = str(e)
                uploaded_file.save()
                messages.error(request, f'Error processing file: {str(e)}')
            
            return redirect('upload_file')
    else:
        form = FileUploadForm()
    
    # Get recent uploads
    recent_uploads = UploadedFile.objects.filter(user=request.user)[:10]
    
    return render(request, 'inventory/upload_file.html', {
        'form': form,
        'recent_uploads': recent_uploads
    })


def process_uploaded_file(uploaded_file):
    """Process uploaded CSV/Excel file"""
    file_path = uploaded_file.file_path.path
    file_type = uploaded_file.file_type
    user = uploaded_file.user
    
    records_processed = 0
    
    if uploaded_file.file_name.endswith('.csv'):
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            records_processed = process_csv_data(reader, file_type, user)
    
    elif uploaded_file.file_name.endswith(('.xlsx', '.xls')):
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        headers = [cell.value for cell in sheet[1]]
        
        data = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            data.append(dict(zip(headers, row)))
        
        records_processed = process_csv_data(data, file_type, user)
    
    return records_processed


def process_csv_data(data, file_type, user):
    """Process CSV data based on file type"""
    records_processed = 0
    
    if file_type == 'stock':
        for row in data:
            if not row.get('product_name'):
                continue
            
            stock, created = Stock.objects.get_or_create(
                user=user,
                product_name=row['product_name'],
                defaults={
                    'quantity': int(row.get('quantity', 0)),
                    'price': float(row.get('price', 0)),
                    'supplier': row.get('supplier', ''),
                    'category': row.get('category', ''),
                    'sku': row.get('sku', ''),
                    'description': row.get('description', ''),
                    'minimum_stock': int(row.get('minimum_stock', 0)),
                }
            )
            
            if not created:
                # Update existing stock
                stock.quantity += int(row.get('quantity', 0))
                stock.price = float(row.get('price', stock.price))
                stock.save()
            
            records_processed += 1
    
    return records_processed
