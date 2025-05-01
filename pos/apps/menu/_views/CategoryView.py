from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pos.apps.menu.models import CategoryModel
from pos.apps.accounts.models import User
from pos.apps.locations.models import LocationModel
from django.shortcuts import get_object_or_404
from pos.utils.logger import POSLogger

logger = POSLogger(__name__)

class CategoryView(APIView):
    def get(self, request):
        """Get all categories"""
        if request.user.is_super_admin:
            categories = CategoryModel.objects.all().order_by('display_order')
            data = [{
                'id': category.id,
                'name': category.name,
                'location_id': category.location.id,
                'display_order': category.display_order
            } for category in categories]
            return Response({'categories': data})
        elif request.user.is_franchise_admin or request.user.is_staff_member:
            requester = get_object_or_404(User, id = request.user.id)
            categories = CategoryModel.objects.filter(location__in=requester.locations.all()).order_by('display_order')
            data = [{
                'id': category.id,
                'name': category.name,
                'location_id': category.location.id,
                'display_order': category.display_order
            } for category in categories]
            return Response({'categories': data})
        else: 
            return Response({'error': 'not allowed'})
    def post(self, request):
        """Create a new category"""
        try:
            requested_location = LocationModel.objects.get(id=request.data.get('location_id'))
            if request.user.is_super_admin:
                category = CategoryModel.objects.create(
                    name=request.data.get('name'),
                    display_order=request.data.get('display_order', 0),
                    location=requested_location
                )
                return Response({
                    'status': 'success',
                    'id': category.id,
                    'name': category.name
                }, status=status.HTTP_201_CREATED)
            elif request.user.is_franchise_admin:
                admin = get_object_or_404(User, id = request.user.id, is_franchise_admin = True)
                locations = list(admin.locations.values('id','name'))
                logger.info(f"\n\n the requested id is {requested_location} \n\n and the access to admin are {locations} \n\n")
                if requested_location.id not in [loc['id'] for loc in locations]:
                    return Response({'error': 'Did not have access for that location'})

                category = CategoryModel.objects.create(
                    name=request.data.get('name'),
                    display_order = request.data.get('display_order', 0),
                    location= requested_location
                )
                return Response({
                    'status': 'success',
                    'id': category.id,
                    'name': category.name
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'not allowed '})
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
