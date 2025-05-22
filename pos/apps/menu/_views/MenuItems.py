from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pos.apps.accounts.models import User
from pos.apps.menu.models import MenuItemModel, CategoryModel
from pos.apps.locations.models import LocationModel
from pos.utils.logger import POSLogger

logger = POSLogger()
class MenuItemsView(APIView):
    def get(self, request):
        """Get all menu items or specific item if ID provided"""
        logger.info(f"i got called bow bow bow")
        item_id = request.data.get('id')
        
        if item_id:
            try:
                item = MenuItemModel.objects.get(pk=item_id, is_available=True)
                if request.user.is_super_admin:
                    data = {
                        'id': item.id,
                        'name': item.name,
                        'price': float(item.price),
                        'category': item.category.name,
                        'location': item.location.id,
                        'image': item.image.url if item.image else None
                    }
                    return Response(data)
                elif request.user.is_franchise_admin:
                    admin = get_object_or_404(User, id=request.user.id, is_franchise_admin=True)
                    if item.location.id not in [loc['id'] for loc in list(admin.locations.values('id', 'name'))]:
                        return Response({'error': 'not allowed'})
                    data = {
                        'id': item.id,
                        'name': item.name,
                        'price': float(item.price),
                        'category': item.category.name,
                        'location': item.location.id,
                        'image': item.image.url if item.image else None
                    }
                    return Response(data)
                else:
                    return Response({'error': 'not allowed'})
            except MenuItemModel.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': 'Menu item not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        if request.user.is_super_admin:
            items = MenuItemModel.objects.filter(is_available=True)
        elif request.user.is_franchise_admin or request.user.is_staff_member:
            requester = get_object_or_404(User, id=request.user.id)
            items = MenuItemModel.objects.filter(
                is_available=True,
                location__in=requester.locations.all()
            )
        else:
            return Response({'error': 'not allowed'})

        data = [{
            'id': item.id,
            'name': item.name,
            'price': float(item.price),
            'category': item.category.name,
            'location_id': item.location.id,
            'image': item.image.url if item.image else None
        } for item in items]
        return Response({'menu_items': data})

    def post(self, request):
        """Create new menu item"""
        try:
            if not (request.user.is_super_admin or request.user.is_franchise_admin):
                return Response({'error': 'not allowed'})

            requested_loc = request.data.get('location_id')
            category = CategoryModel.objects.get(id=request.data.get('category_id'))
            
            if category.location.id != requested_loc:
                return Response({'error': 'category does not belong this location'})
                
            location = LocationModel.objects.get(id=requested_loc)
            
            # Check location access for franchise admin
            if request.user.is_franchise_admin:
                admin = get_object_or_404(User, id=request.user.id, is_franchise_admin=True)
                if requested_loc not in [loc['id'] for loc in list(admin.locations.values('id', 'name'))]:
                    return Response({'error': 'does not have access to this location'})

            # Create menu item
            new_item = MenuItemModel.objects.create(
                name=request.data.get('name'),
                price=request.data.get('price'),
                category=category,
                location=location,
                is_available=True
            )
            
            return Response({
                'status': 'success',
                'id': new_item.id,
                'name': new_item.name
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        """Update menu item"""
        try:
            item = MenuItemModel.objects.get(pk=request.data.get('id'))
            if 'name' in request.data:
                item.name = request.data.get('name')
            if 'price' in request.data:
                item.price = request.data.get('price')
            if 'category_id' in request.data:
                item.category = CategoryModel.objects.get(id=request.data.get('category_id'))
            if 'location_id' in request.data:
                item.location = LocationModel.objects.get(id=request.data.get('location_id'))
            
            item.save()
            return Response({'status': 'success'})
        
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request):
        """delete menu item"""
        try:
            item = MenuItemModel.objects.get(pk=request.data.get('id'))
            item.delete()
            return Response({'status': 'success'})
        
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )