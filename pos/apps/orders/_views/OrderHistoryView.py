from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from pos.apps.orders.models import Order, OrderItem
from django.shortcuts import get_object_or_404

class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get order history with various filters
        Params:
            - location_id: Filter by location
            - date_from: Filter by date range (YYYY-MM-DD)
            - date_to: Filter by date range (YYYY-MM-DD)
            - order_id: Get specific order details
        """
        user = request.user
        order_id = request.query_params.get('order_id')
        
        # If order_id is provided, return detailed information about that order
        if order_id:
            try:
                # Apply permissions based on user role
                if hasattr(user, 'is_super_admin') and user.is_super_admin:
                    order = get_object_or_404(Order, id=order_id)
                elif hasattr(user, 'is_franchise_admin') and (user.is_franchise_admin or user.is_staff_member):
                    # Only see orders from locations they have access to
                    user_locations = user.locations.all()
                    order = get_object_or_404(Order, id=order_id, location__in=user_locations)
                else:
                    order = get_object_or_404(Order, id=order_id)
                
                # Get order items
                order_items = order.items.all().values(
                    'id', 'menu_item_id', 'quantity', 'price'
                )
                
                # Add menu item name if available
                for item in order_items:
                    menu_item = order.items.get(id=item['id']).menu_item
                    item['menu_item__name'] = menu_item.name if menu_item else None
                    item['order_id'] = order.id
                
                response_data = {
                    'id': order.id,
                    'order_number': order.order_number,
                    'order_date': order.order_date,
                    'total_amount': order.total_amount,
                    'location': {
                        'id': order.location.id,
                        'name': order.location.name
                    },
                    'location_name': order.location.name,
                    'items': list(order_items)
                }
                
                # Add processor information if available
                if order.processed_by:
                    response_data['processed_by'] = {
                        'id': order.processed_by.id,
                        'name': f"{order.processed_by.first_name} {order.processed_by.last_name}"
                    }
                
                return Response(response_data)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        # Otherwise, return filtered list of orders
        try:
            # Apply filters
            location_id = request.query_params.get('location_id')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Base queryset with role-based filtering
            if hasattr(user, 'is_super_admin') and user.is_super_admin:
                orders = Order.objects.all()
            elif hasattr(user, 'is_franchise_admin') and (user.is_franchise_admin or user.is_staff_member):
                user_locations = user.locations.all()
                orders = Order.objects.filter(location__in=user_locations)
            else:
                orders = Order.objects.all()
            
            # Apply additional filters
            if location_id:
                if not hasattr(user, 'is_super_admin') or user.is_super_admin or \
                   (hasattr(user, 'locations') and user.locations.filter(id=location_id).exists()):
                    orders = orders.filter(location_id=location_id)
                else:
                    return Response({"error": "You don't have access to this location"}, 
                                   status=status.HTTP_403_FORBIDDEN)
            
            # Date range filtering
            if date_from:
                orders = orders.filter(order_date__gte=date_from)
            if date_to:
                orders = orders.filter(order_date__lte=f"{date_to} 23:59:59")
            
            # Order by date, newest first
            orders = orders.order_by('-order_date')
            
            # Serialize the data
            response_data = []
            for order in orders:
                order_data = {
                    'id': order.id,
                    'order_number': order.order_number,
                    'order_date': order.order_date,
                    'total_amount': order.total_amount,
                    'location_name': order.location.name,
                }
                response_data.append(order_data)
            
            return Response(response_data)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 