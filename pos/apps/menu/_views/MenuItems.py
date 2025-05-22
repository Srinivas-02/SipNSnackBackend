from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pos.apps.accounts.models import User
from pos.apps.menu.models import MenuItemModel, CategoryModel
from pos.apps.locations.models import LocationModel
from pos.utils.logger import POSLogger

logger = POSLogger(__name__)

class MenuItemsView(APIView):
    def get(self, request):
        """Get all menu items or specific item if ID provided"""
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
                elif request.user.is_franchise_admin or request.user.is_staff_member:
                    user = get_object_or_404(User, id=request.user.id)
                    if item.location.id not in [loc['id'] for loc in list(user.locations.values('id', 'name'))]:
                        logger.warning(f"User {request.user.email} attempted to access unauthorized menu item {item_id}")
                        return Response({'error': 'You do not have access to this menu item'}, status=status.HTTP_403_FORBIDDEN)
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
                    logger.warning(f"Unauthorized access attempt by {request.user.email}")
                    return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            except MenuItemModel.DoesNotExist:
                logger.warning(f"Attempt to access non-existent menu item {item_id} by {request.user.email}")
                return Response(
                    {'status': 'error', 'message': 'Menu item not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        if request.user.is_super_admin:
            items = MenuItemModel.objects.filter(is_available=True)
        elif request.user.is_franchise_admin or request.user.is_staff_member:
            user = get_object_or_404(User, id=request.user.id)
            items = MenuItemModel.objects.filter(
                is_available=True,
                location__in=user.locations.all()
            )
        else:
            logger.warning(f"Unauthorized access attempt by {request.user.email}")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        data = [{
            'id': item.id,
            'name': item.name,
            'price': float(item.price),
            'category': item.category.name,
            'location_id': item.location.id,
            'image': item.image.url if item.image else None
        } for item in items]
        logger.info(f"Menu items list accessed by {request.user.email}")
        return Response({'menu_items': data})

    def post(self, request):
        """Create new menu item"""
        try:
            if not (request.user.is_super_admin or request.user.is_franchise_admin):
                logger.warning(f"Unauthorized create attempt by {request.user.email}")
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

            requested_loc = request.data.get('location_id')
            category = CategoryModel.objects.get(id=request.data.get('category_id'))
            
            if category.location.id != requested_loc:
                logger.warning(f"Category {category.id} does not belong to location {requested_loc} in create attempt by {request.user.email}")
                return Response({'error': 'Category does not belong to this location'}, status=status.HTTP_400_BAD_REQUEST)
                
            location = LocationModel.objects.get(id=requested_loc)
            
            # Check location access for franchise admin
            if request.user.is_franchise_admin:
                admin = get_object_or_404(User, id=request.user.id, is_franchise_admin=True)
                if requested_loc not in [loc['id'] for loc in list(admin.locations.values('id', 'name'))]:
                    logger.warning(f"Franchise admin {request.user.email} attempted to create menu item in unauthorized location {requested_loc}")
                    return Response({'error': 'You do not have access to this location'}, status=status.HTTP_403_FORBIDDEN)

            # Create menu item
            new_item = MenuItemModel.objects.create(
                name=request.data.get('name'),
                price=request.data.get('price'),
                category=category,
                location=location,
                is_available=True
            )
            
            logger.info(f"New menu item '{new_item.name}' created by {request.user.email}")
            return Response({
                'status': 'success',
                'id': new_item.id,
                'name': new_item.name
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating menu item: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        """Update menu item"""
        try:
            if not (request.user.is_super_admin or request.user.is_franchise_admin):
                logger.warning(f"Unauthorized update attempt by {request.user.email}")
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

            item = MenuItemModel.objects.get(pk=request.data.get('id'))
            
            # Check location access for franchise admin
            if request.user.is_franchise_admin:
                admin = get_object_or_404(User, id=request.user.id, is_franchise_admin=True)
                current_location = item.location.id
                new_location = request.data.get('location_id', current_location)
                if new_location not in [loc['id'] for loc in list(admin.locations.values('id', 'name'))]:
                    logger.warning(f"Franchise admin {request.user.email} attempted to update menu item {item.id} to unauthorized location {new_location}")
                    return Response({'error': 'You do not have access to this location'}, status=status.HTTP_403_FORBIDDEN)

            if 'name' in request.data:
                item.name = request.data.get('name')
            if 'price' in request.data:
                item.price = request.data.get('price')
            if 'category_id' in request.data:
                category = CategoryModel.objects.get(id=request.data.get('category_id'))
                new_location = request.data.get('location_id', item.location.id)
                if category.location.id != new_location:
                    logger.warning(f"Category {category.id} does not belong to location {new_location} in update attempt by {request.user.email}")
                    return Response({'error': 'Category does not belong to this location'}, status=status.HTTP_400_BAD_REQUEST)
                item.category = category
            if 'location_id' in request.data:
                item.location = LocationModel.objects.get(id=request.data.get('location_id'))
            
            item.save()
            logger.info(f"Menu item '{item.name}' updated by {request.user.email}")
            return Response({'status': 'success'})
        
        except Exception as e:
            logger.error(f"Error updating menu item: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request):
        """Delete menu item (Super Admin or Franchise Admin with location access)"""
        try:
            if not (request.user.is_super_admin or request.user.is_franchise_admin):
                logger.warning(f"Unauthorized delete attempt by {request.user.email}")
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

            if 'id' not in request.data:
                logger.warning(f"Attempt to delete menu item without ID by {request.user.email}")
                return Response(
                    {'status': 'error', 'message': 'Menu item ID required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            item = get_object_or_404(MenuItemModel, pk=request.data.get('id'))
            
            # Check location access for franchise admin
            if request.user.is_franchise_admin:
                admin = get_object_or_404(User, id=request.user.id, is_franchise_admin=True)
                admin_location_ids = [loc['id'] for loc in admin.locations.values('id')]
                if item.location.id not in admin_location_ids:
                    logger.warning(f"Franchise admin {request.user.email} attempted to delete menu item {item.id} from unauthorized location {item.location.id}")
                    return Response(
                        {'status': 'error', 'message': 'You do not have access to this menu item’s location'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            item_name = item.name
            item.delete()
            logger.info(f"Menu item '{item_name}' deleted by {request.user.email}")
            return Response({'status': 'success'}, status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            logger.error(f"Error deleting menu item: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )