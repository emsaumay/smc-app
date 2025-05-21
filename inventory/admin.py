from django.contrib import admin
from .models import Stock, Sale, UploadedFile, UserProfile


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'quantity', 'price', 'supplier', 'user', 'is_low_stock', 'created_at']
    list_filter = ['user', 'supplier', 'category', 'created_at']
    search_fields = ['product_name', 'sku', 'supplier']
    list_editable = ['quantity', 'price']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_sold', 'unit_price', 'total_amount', 'customer_name', 'sale_date', 'user']
    list_filter = ['user', 'sale_date', 'product__category']
    search_fields = ['product__product_name', 'customer_name', 'customer_phone']
    ordering = ['-sale_date']
    readonly_fields = ['total_amount']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'file_type', 'records_processed', 'processing_status', 'uploaded_at', 'user']
    list_filter = ['processing_status', 'file_type', 'uploaded_at', 'user']
    search_fields = ['file_name']
    readonly_fields = ['records_processed', 'uploaded_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'phone', 'currency', 'created_at']
    search_fields = ['user__username', 'company_name']
