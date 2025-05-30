from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from pos.apps.orders.models import Order, OrderItem
from pos.apps.menu.models import MenuItemModel
from pos.apps.locations.models import LocationModel
import random

class OrderView(APIView):
    def post(self, request):
        # Extract basic order data
        data = request.data
        location_id = data.get('location_id')
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
                'price': item_price
            })

        # Create order
        try:
            order = Order.objects.create(
                location=location,
                total_amount=total_amount,
                processed_by=request.user if request.user.is_authenticated else None
            )
            
            # Create order items
            for item in order_items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=item['menu_item'],
                    quantity=item['quantity'],
                    price=item['price']
                )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'order_id': order.id,
            'total_amount': str(order.total_amount),
            'order_items': order.items.values(),
            'order_date': order.order_date,
            'message': 'Order created successfully',
        }, status=status.HTTP_201_CREATED)