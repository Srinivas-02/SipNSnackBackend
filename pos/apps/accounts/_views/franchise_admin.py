from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pos.apps.accounts.models import User
from pos.apps.locations.models import LocationModel

class FranchiseAdminView(APIView):
    """
    Handles franchise admin operations:
    - POST: Create franchise admin
    - GET: List all franchise admins or get specific one
    - PATCH: Update franchise admin
    - DELETE: Deactivate franchise admin
    """
    
    def post(self, request):
        """Create new franchise admin"""
        required_fields = ['email', 'password', 'first_name', 'last_name']
        if missing := [f for f in required_fields if f not in request.data]:
            return Response(
                {'error': f'Missing fields: {", ".join(missing)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            franchise_admin = User.objects.create_user(
                email=request.data['email'],
                password=request.data['password'],
                first_name=request.data['first_name'],
                last_name=request.data['last_name'],
                is_franchise_admin=True
            )

            if 'location_ids' in request.data:
                locations = LocationModel.objects.filter(id__in=request.data['location_ids'])
                franchise_admin.locations.set(locations)

            return Response({
                'id': franchise_admin.id,
                'email': franchise_admin.email,
                'message': 'Franchise admin created successfully'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request):
        """Get all franchise admins or specific one"""
        admin_id = request.query_params.get('id')
        
        if admin_id:
            admin = get_object_or_404(User, id=admin_id, is_franchise_admin=True)
            locations = list(admin.locations.values('id', 'name'))
            
            return Response({
                'id': admin.id,
                'email': admin.email,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'locations': locations
            })
        else:
            admins = User.objects.filter(is_franchise_admin=True).values(
                'id', 'email', 'first_name', 'last_name'
            )
            return Response(list(admins))

    def patch(self, request):
        """Update franchise admin details"""
        if 'id' not in request.data:
            return Response(
                {'error': 'Franchise admin ID required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        admin = get_object_or_404(User, id=request.data['id'], is_franchise_admin=True)
        
        for field in ['first_name', 'last_name', 'email']:
            if field in request.data:
                setattr(admin, field, request.data[field])
        
        if 'location_ids' in request.data:
            locations = LocationModel.objects.filter(id__in=request.data['location_ids'])
            admin.locations.set(locations)
        
        admin.save()
        return Response({'message': 'Franchise admin updated'})

    def delete(self, request):
            """Permanently delete franchise admin from database"""
            if 'id' not in request.query_params:
                return Response(
                    {'error': 'Specify ?id=<franchise_admin_id>'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            admin = get_object_or_404(User, id=request.query_params['id'], is_franchise_admin=True)
            admin.delete()  
            return Response(
                {'message': 'Franchise admin permanently deleted'},
                status=status.HTTP_204_NO_CONTENT
            )