# menu/models.py
from django.db import models
from pos.apps.locations.models import LocationModel

class CategoryModel(models.Model):
    """Simple food categories like Breakfast, Coffee, Meals, etc."""
    name = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)
    location = models.ForeignKey(LocationModel, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)  
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order']

    def __str__(self):
        return self.name

class MenuItemModel(models.Model):
    """Basic menu items that can be ordered"""
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    image = models.BinaryField(null=True, blank=True)
    location = models.ForeignKey(LocationModel, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['category__display_order', 'name']

    def __str__(self):
        return f"{self.name} - ₹{self.price}"