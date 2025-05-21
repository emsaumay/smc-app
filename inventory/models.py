from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Stock(models.Model):
    """Stock/Product inventory model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stocks')
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    sku = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    minimum_stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'product_name']  # Prevent duplicate products per user
    
    def __str__(self):
        return f"{self.product_name} ({self.quantity})"
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock


class Sale(models.Model):
    """Sales transaction model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    product = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='sales')
    quantity_sold = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    sale_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-sale_date']
    
    def __str__(self):
        return f"Sale: {self.product.product_name} x{self.quantity_sold} - ${self.total_amount}"
    
    def save(self, *args, **kwargs):
        # Calculate total amount if not provided
        if not self.total_amount:
            self.total_amount = self.quantity_sold * self.unit_price
        
        # Update stock quantity when sale is created
        if not self.pk:  # Only on creation
            self.product.quantity -= self.quantity_sold
            self.product.save()
        
        super().save(*args, **kwargs)


class UploadedFile(models.Model):
    """Model to track file uploads"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploads')
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='uploads/')
    file_type = models.CharField(max_length=50)
    records_processed = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(default=timezone.now)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.file_name} - {self.processing_status}"


class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=3, default='USD')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
