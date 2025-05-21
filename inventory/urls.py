from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    
    # Stock management
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/add/', views.add_stock, name='add_stock'),
    path('stock/edit/<int:stock_id>/', views.edit_stock, name='edit_stock'),
    path('stock/query/', views.stock_query, name='stock_query'),
    
    # Sales management
    path('sales/', views.sales_list, name='sales_list'),
    path('sales/add/', views.add_sale, name='add_sale'),
    
    # File upload
    path('upload/', views.upload_file, name='upload_file'),
]