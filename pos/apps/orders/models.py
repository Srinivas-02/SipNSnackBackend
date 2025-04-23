from django.db import models
from pos.apps.locations.models import LocationModel
from pos.apps.menu.models import MenuItemModel

# Create your models here.
class Order(models.Model):
    location = models.ForeignKey(LocationModel, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=50)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    table_number = models.CharField(max_length=10, blank=True)
    customer_name = models.CharField(max_length=100, blank=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItemModel, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)