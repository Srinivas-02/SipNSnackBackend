from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from pos.apps.orders.models import Order, OrderItem
from pos.apps.menu.models import MenuItemModel
from pos.apps.locations.models import LocationModel
import random

def generate_order_number(location):
    """Generate unique order number with location ID and timestamp"""
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S%f")
    return f"ORD-{location.id}-{timestamp}-{random.randint(1000,9999)}"

class OrderView(APIView):
    def post(self, request):
        # Extract basic order data
        data = request.data
        location_id = data.get('location_id')
        table_number = data.get('table_number', '')
        customer_name = data.get('customer_name', '')
        items = data.get('items', [])

        # Validate location
        try:
            location = LocationModel.objects.get(id=location_id)
        except LocationModel.DoesNotExist:
            return Response(
                {"error": "Invalid location ID"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate items
        if not items:
            return Response(
                {"error": "No items in order"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        total_amount = 0
        order_items = []

        # Process each item
        for item in items:
            menu_item_id = item.get('menu_item_id')
            quantity = item.get('quantity', 1)
            notes = item.get('notes', '')

            try:
                menu_item = MenuItemModel.objects.get(id=menu_item_id)
            except MenuItemModel.DoesNotExist:
                return Response(
                    {"error": f"Invalid menu item ID: {menu_item_id}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate item total
            item_price = menu_item.price
            total_amount += item_price * quantity

            # Store item details
            order_items.append({
                'menu_item': menu_item,
                'quantity': quantity,
                'price': item_price,
                'notes': notes
            })

        # Create order
        try:
            order = Order.objects.create(
                location=location,
                order_number=generate_order_number(location),
                total_amount=total_amount,
                table_number=table_number,
                customer_name=customer_name
            )
            
            # Create order items
            for item in order_items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=item['menu_item'],
                    quantity=item['quantity'],
                    price=item['price'],
                    notes=item['notes']
                )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'order_id': order.id,
            'order_number': order.order_number,
            'total_amount': str(order.total_amount),
            'order_items': order.items.values(),
            'message': 'Order created successfully'
        }, status=status.HTTP_201_CREATED)