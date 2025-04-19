from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pos.apps.menu.models import CategoryModel
from pos.apps.locations.models import LocationModel

class CategoryView(APIView):
    def get(self, request):
        """Get all categories"""
        categories = CategoryModel.objects.all().order_by('display_order')
        data = [{
            'id': category.id,
            'name': category.name,
            'location': category.location.id,
            'display_order': category.display_order
        } for category in categories]
        return Response({'categories': data})

    def post(self, request):
        """Create a new category"""
        try:
            location = LocationModel.objects.get(id=request.data.get('location_id'))
            category = CategoryModel.objects.create(
                name=request.data.get('name'),
                display_order=request.data.get('display_order', 0),
                location=location
            )
            return Response({
                'status': 'success',
                'id': category.id,
                'name': category.name
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
