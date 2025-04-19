from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pos.apps.menu.models import MenuItemModel, CategoryModel
from pos.apps.locations.models import LocationModel

class MenuItemsView(APIView):
    def get(self, request):
        """Get all menu items or specific item if ID provided"""
        item_id = request.data.get('id')
        
        if item_id:
            try:
                item = MenuItemModel.objects.get(pk=item_id, is_available=True)
                data = {
                    'id': item.id,
                    'name': item.name,
                    'price': float(item.price),
                    'category': item.category.name,
                    'location': item.location.id,
                    'image': item.image.url if item.image else None
                }
                return Response(data)
            except MenuItemModel.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': 'Menu item not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        items = MenuItemModel.objects.filter(is_available=True)
        data = [{
            'id': item.id,
            'name': item.name,
            'price': float(item.price),
            'category': item.category.name,
            'location': item.location.id,
            'image': item.image.url if item.image else None
        } for item in items]
        return Response({'menu_items': data})

    def post(self, request):
        """Create new menu item"""
        try:
            category = CategoryModel.objects.get(id=request.data.get('category_id'))
            location = LocationModel.objects.get(id=request.data.get('location_id'))
            
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