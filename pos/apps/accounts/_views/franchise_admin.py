from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pos.apps.accounts.models import User
from pos.apps.locations.models import LocationModel
from pos.utils.logger import POSLogger

logger = POSLogger(__name__)

class FranchiseAdminView(APIView):
    """
    Handles franchise admin operations:
    - POST: Create franchise admin (Super Admin only)
    - GET: List all franchise admins or get specific one (Super Admin or Franchise Admin)
    - PATCH: Update franchise admin (Super Admin only)
    - DELETE: Delete franchise admin (Super Admin only)
    
    Protected: Super Admins have full access; Franchise Admins can view (location-restricted); Staff and others are denied.
    """
    
    def post(self, request):
        """Create new franchise admin (Super Admin only)"""
        # Restrict to Super Admins
        if not request.user.is_super_admin:
            logger.warning(f"Unauthorized user {request.user.email} attempted to create franchise admin")
            return Response(
                {'error': 'Not authorized to create franchise admins'},
                status=status.HTTP_403_FORBIDDEN
            )

        required_fields = ['email', 'password', 'first_name', 'last_name', 'location_ids']
        if missing := [f for f in required_fields if f not in request.data]:
            logger.warning(f"Attempt to create franchise admin with missing fields: {missing} by {request.user.email}")
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
                if len(locations) != len(request.data['location_ids']):
                    logger.warning(f"Invalid location IDs in franchise admin creation by {request.user.email}")
                    return Response(
                        {'error': 'One or more location IDs are invalid'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                franchise_admin.locations.set(locations)

            logger.info(f"Franchise admin {franchise_admin.email} created by super admin {request.user.email}")
            return Response({
                'id': franchise_admin.id,
                'email': franchise_admin.email,
                'message': 'Franchise admin created successfully'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating franchise admin: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request):
        """Get all franchise admins or specific one"""
        # Deny Staff users
        if request.user.is_staff_member:
            logger.warning(f"Staff user {request.user.email} attempted to access franchise admins")
            return Response(
                {'error': 'Not authorized to view franchise admins'},
                status=status.HTTP_403_FORBIDDEN
            )

        admin_id = request.query_params.get('id')
        if admin_id:
            try:
                admin = get_object_or_404(User, id=admin_id, is_franchise_admin=True)
                
                # For Franchise Admins, check location overlap
                if request.user.is_franchise_admin:
                    user_locations = request.user.locations.all()
                    admin_locations = admin.locations.all()
                    if not any(loc in user_locations for loc in admin_locations):
                        logger.warning(f"Franchise admin {request.user.email} attempted to access unauthorized franchise admin {admin.email}")
                        return Response(
                            {'error': 'You do not have access to this franchise admin'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                
                locations = list(admin.locations.values('id', 'name'))
                
                logger.info(f"Franchise admin {admin.email} details accessed by {request.user.email}")
                return Response({
                    'id': admin.id,
                    'email': admin.email,
                    'first_name': admin.first_name,
                    'last_name': admin.last_name,
                    'locations': locations
                })
            except Exception as e:
                logger.warning(f"Error retrieving franchise admin {admin_id}: {str(e)}")
                return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        else:
            if request.user.is_super_admin:
                # Get all franchise admins
                franchise_admins = User.objects.filter(is_franchise_admin=True)
                
                admins_data = []
                for admin in franchise_admins:
                    admin_locations = list(admin.locations.values('id', 'name'))
                    admins_data.append({
                        'id': admin.id,
                        'email': admin.email,
                        'first_name': admin.first_name,
                        'last_name': admin.last_name,
                        'locations': admin_locations
                    })
                
                logger.info(f"All franchise admins list accessed by super admin {request.user.email}")
                return Response(admins_data)
            
            elif request.user.is_franchise_admin:
                admin = get_object_or_404(User, id=request.user.id, is_franchise_admin=True)
                
                # Get all franchise admins that have access to any of these locations
                franchise_admins = User.objects.filter(
                    is_franchise_admin=True,
                    locations__in=admin.locations.all()
                ).distinct()
                
                admins_data = []
                for admin in franchise_admins:
                    admin_locations = list(admin.locations.values('id', 'name'))
                    admins_data.append({
                        'id': admin.id,
                        'email': admin.email,
                        'first_name': admin.first_name,
                        'last_name': admin.last_name,
                        'locations': admin_locations
                    })
                
                logger.info(f"Franchise admins list accessed by franchise admin {request.user.email}")
                return Response(admins_data)
            
            else:
                logger.warning(f"Unauthorized user {request.user.email} attempted to list franchise admins")
                return Response(
                    {'error': 'Not authorized to view franchise admins'},
                    status=status.HTTP_403_FORBIDDEN
                )

    def patch(self, request):
        """Update franchise admin details (Super Admin only)"""
        # Deny Staff users
        if request.user.is_staff_member:
            logger.warning(f"Staff user {request.user.email} attempted to update franchise admin")
            return Response(
                {'error': 'Not authorized to update franchise admins'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Restrict to Super Admins
        if not request.user.is_super_admin:
            logger.warning(f"Unauthorized user {request.user.email} attempted to update franchise admin")
            return Response(
                {'error': 'Not authorized to update franchise admins'},
                status=status.HTTP_403_FORBIDDEN
            )

        if 'id' not in request.data:
            logger.warning(f"Attempt to update franchise admin without ID by {request.user.email}")
            return Response(
                {'error': 'Franchise admin ID required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            admin = get_object_or_404(User, id=request.data['id'], is_franchise_admin=True)
            
            for field in ['first_name', 'last_name', 'email']:
                if field in request.data:
                    setattr(admin, field, request.data[field])
            
            if 'location_ids' in request.data:
                locations = LocationModel.objects.filter(id__in=request.data['location_ids'])
                if len(locations) != len(request.data['location_ids']):
                    logger.warning(f"Invalid location IDs in franchise admin update by {request.user.email}")
                    return Response(
                        {'error': 'One or more location IDs are invalid'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                admin.locations.set(locations)
            
            # Update password if provided
            if 'password' in request.data:
                admin.set_password(request.data['password'])
            
            admin.save()
            
            locations = list(admin.locations.values('id', 'name'))
            logger.info(f"Franchise admin {admin.email} updated by super admin {request.user.email}")
            return Response({
                'message': 'Franchise admin updated successfully',
                'id': admin.id,
                'email': admin.email,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'locations': locations
            })
        except Exception as e:
            logger.error(f"Error updating franchise admin: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        """Delete franchise admin (Super Admin only)"""
        # Deny Staff users
        if request.user.is_staff_member:
            logger.warning(f"Staff user {request.user.email} attempted to delete franchise admin")
            return Response(
                {'error': 'Not authorized to delete franchise admins'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Restrict to Super Admins
        if not request.user.is_super_admin:
            logger.warning(f"Unauthorized user {request.user.email} attempted to delete franchise admin")
            return Response(
                {'error': 'Not authorized to delete franchise admins'},
                status=status.HTTP_403_FORBIDDEN
            )

        if 'id' not in request.query_params:
            logger.warning(f"Attempt to delete franchise admin without ID by {request.user.email}")
            return Response(
                {'error': 'Specify ?id=<franchise_admin_id>'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            admin = get_object_or_404(User, id=request.query_params['id'], is_franchise_admin=True)
            admin_email = admin.email
            admin.delete()
            logger.info(f"Franchise admin {admin_email} deleted by super admin {request.user.email}")
            return Response(
                {'message': 'Franchise admin deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f"Error deleting franchise admin: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)