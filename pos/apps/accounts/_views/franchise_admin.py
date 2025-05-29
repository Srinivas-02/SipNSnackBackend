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
    - POST: Create franchise admin with optional locations
    - GET: List admins created by user with same locations or self
    - PATCH: Update admins (self or created with same locations)
    - DELETE: Delete admins (created with same locations)
    """

    def post(self, request):
        """Create a new franchise admin"""
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated attempt to create admin")
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not (request.user.is_super_admin or request.user.is_franchise_admin):
            logger.warning(f"Unauthorized user {request.user.email} attempted to create admin")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        required_fields = ['email', 'password', 'first_name', 'last_name']
        if missing := [f for f in required_fields if f not in request.data]:
            logger.warning(f"Missing fields: {missing} by {request.user.email}")
            return Response({'error': f'Missing fields: {", ".join(missing)}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            franchise_admin = User.objects.create_user(
                email=request.data['email'],
                password=request.data['password'],
                first_name=request.data['first_name'],
                last_name=request.data['last_name'],
                is_franchise_admin=True,
                created_by=request.user
            )

            if request.data.get('location_ids'):
                location_ids = request.data['location_ids']
                if not isinstance(location_ids, list):
                    logger.warning(f"Invalid location_ids format by {request.user.email}")
                    franchise_admin.delete()
                    return Response({'error': 'location_ids must be a list'}, status=status.HTTP_400_BAD_REQUEST)
                
                if request.user.is_franchise_admin:
                    user_locations = set(request.user.locations.values_list('id', flat=True))
                    logger.debug(f"User {request.user.email} locations: {user_locations}")
                    if not all(isinstance(loc_id, int) and loc_id in user_locations for loc_id in location_ids):
                        logger.warning(f"Invalid locations {location_ids} by {request.user.email}")
                        franchise_admin.delete()
                        return Response({'error': 'Invalid location access'}, status=status.HTTP_403_FORBIDDEN)

                locations = LocationModel.objects.filter(id__in=location_ids)
                if len(locations) != len(location_ids):
                    logger.warning(f"Invalid location IDs {location_ids} by {request.user.email}")
                    franchise_admin.delete()
                    return Response({'error': 'Invalid location IDs'}, status=status.HTTP_400_BAD_REQUEST)
                
                franchise_admin.locations.set(locations)
                logger.debug(f"Assigned locations to {franchise_admin.email}: {location_ids}")

            logger.info(f"Created admin {franchise_admin.email} by {request.user.email}")
            return Response({
                'id': franchise_admin.id,
                'email': franchise_admin.email,
                'message': 'Admin created',
                'locations': list(franchise_admin.locations.values('id', 'name'))
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating admin: {str(e)}")
            return Response({'error': 'Failed to create admin'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """Get admins created by user with same locations or self"""
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated access attempt")
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.is_staff_member:
            logger.warning(f"Staff user {request.user.email} attempted access")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        admin_id = request.query_params.get('id')
        if admin_id:
            try:
                admin = get_object_or_404(User, id=admin_id, is_franchise_admin=True)
                if request.user.is_franchise_admin:
                    user_locations = set(request.user.locations.values_list('id', flat=True))
                    admin_locations = set(admin.locations.values_list('id', flat=True))
                    created_by_id = admin.created_by.id if admin.created_by else None
                    logger.debug(f"Get admin {admin.email} by {request.user.email}: user_locations={user_locations}, admin_locations={admin_locations}, created_by={created_by_id}")
                    if not (admin == request.user or (admin.created_by == request.user and admin_locations.issubset(user_locations))):
                        logger.warning(f"Unauthorized access by {request.user.email} to {admin.email}")
                        return Response({'error': 'No access'}, status=status.HTTP_403_FORBIDDEN)
                
                return Response({
                    'id': admin.id,
                    'email': admin.email,
                    'first_name': admin.first_name,
                    'last_name': admin.last_name,
                    'locations': list(admin.locations.values('id', 'name'))
                })
            except Exception as e:
                logger.error(f"Error getting admin {admin_id}: {str(e)}")
                return Response({'error': 'Failed to get admin'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            try:
                if request.user.is_super_admin:
                    logger.debug(f"Super admin {request.user.email} fetching all admins")
                    franchise_admins = User.objects.filter(is_franchise_admin=True)
                elif request.user.is_franchise_admin:
                    user_locations = set(request.user.locations.values_list('id', flat=True))
                    logger.debug(f"List admins for {request.user.email}: user_locations={user_locations}")
                    # Fetch admins created by user with shared locations
                    franchise_admins = User.objects.filter(
                        is_franchise_admin=True,
                        created_by=request.user
                    ).distinct()
                    # Filter admins to only include those with locations subset of user's locations
                    valid_admins = []
                    for admin in franchise_admins:
                        admin_locations = set(admin.locations.values_list('id', flat=True))
                        if admin_locations.issubset(user_locations):
                            valid_admins.append(admin)
                    # Include self
                    if request.user.is_franchise_admin:
                        valid_admins.append(request.user)
                    franchise_admins = valid_admins
                else:
                    logger.warning(f"Unauthorized list by {request.user.email}")
                    return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

                admins_data = [{
                    'id': admin.id,
                    'email': admin.email,
                    'first_name': admin.first_name,
                    'last_name': admin.last_name,
                    'locations': list(admin.locations.values('id', 'name'))
                } for admin in franchise_admins]
                logger.info(f"Admins listed by {request.user.email}: {len(admins_data)} admins")
                return Response(admins_data)
            except Exception as e:
                logger.error(f"Error listing admins for {request.user.email}: {str(e)}")
                return Response({'error': 'Failed to list admins'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        """Update admin (self or created with same locations)"""
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated update attempt")
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.is_staff_member:
            logger.warning(f"Staff user {request.user.email} attempted update")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        if not (request.user.is_super_admin or request.user.is_franchise_admin):
            logger.warning(f"Unauthorized update by {request.user.email}")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        if 'id' not in request.data:
            logger.warning(f"No ID provided by {request.user.email}")
            return Response({'error': 'Admin ID required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            admin = get_object_or_404(User, id=request.data['id'], is_franchise_admin=True)
            if request.user.is_franchise_admin:
                user_locations = set(request.user.locations.values_list('id', flat=True))
                admin_locations = set(admin.locations.values_list('id', flat=True))
                created_by_id = admin.created_by.id if admin.created_by else None
                logger.debug(f"Update {admin.email} by {request.user.email}: user_locations={user_locations}, admin_locations={admin_locations}, created_by={created_by_id}")
                if not (admin == request.user or (admin.created_by == request.user and admin_locations.issubset(user_locations))):
                    logger.warning(f"Unauthorized update by {request.user.email} to {admin.email}")
                    return Response({'error': 'No access'}, status=status.HTTP_403_FORBIDDEN)

                if 'location_ids' in request.data and request.data.get('location_ids') and admin != request.user:
                    if not isinstance(request.data['location_ids'], list):
                        logger.warning(f"Invalid location_ids by {request.user.email}")
                        return Response({'error': 'location_ids must be a list'}, status=status.HTTP_400_BAD_REQUEST)
                    if not all(isinstance(loc_id, int) and loc_id in user_locations for loc_id in request.data['location_ids']):
                        logger.warning(f"Invalid locations {request.data['location_ids']} by {request.user.email}")
                        return Response({'error': 'Invalid location access'}, status=status.HTTP_403_FORBIDDEN)

            for field in ['first_name', 'last_name', 'email']:
                if field in request.data:
                    setattr(admin, field, request.data[field])

            if 'location_ids' in request.data and request.data.get('location_ids'):
                locations = LocationModel.objects.filter(id__in=request.data['location_ids'])
                if len(locations) != len(request.data['location_ids']):
                    logger.warning(f"Invalid location IDs {request.data['location_ids']} by {request.user.email}")
                    return Response({'error': 'Invalid location IDs'}, status=status.HTTP_400_BAD_REQUEST)
                admin.locations.set(locations)

            if 'password' in request.data:
                admin.set_password(request.data['password'])

            admin.save()
            logger.info(f"Admin {admin.email} updated by {request.user.email}")
            return Response({
                'message': 'Admin updated',
                'id': admin.id,
                'email': admin.email,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'locations': list(admin.locations.values('id', 'name'))
            })
        except Exception as e:
            logger.error(f"Error updating admin: {str(e)}")
            return Response({'error': 'Failed to update admin'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """Delete admin (created with same locations)"""
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated delete attempt")
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.is_staff_member:
            logger.warning(f"Staff user {request.user.email} attempted delete")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        if not (request.user.is_super_admin or request.user.is_franchise_admin):
            logger.warning(f"Unauthorized delete by {request.user.email}")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        if 'id' not in request.query_params:
            logger.warning(f"No ID provided by {request.user.email}")
            return Response({'error': 'Admin ID required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            admin = get_object_or_404(User, id=request.query_params.get('id'), is_franchise_admin=True)
            if request.user.is_franchise_admin:
                user_locations = set(request.user.locations.values_list('id', flat=True))
                admin_locations = set(admin.locations.values_list('id', flat=True))
                created_by_id = admin.created_by.id if admin.created_by else None
                logger.debug(f"Delete {admin.email} by {request.user.email}: user_locations={user_locations}, admin_locations={admin_locations}, created_by={created_by_id}")
                if not (admin.created_by == request.user and admin_locations.issubset(user_locations)):
                    logger.warning(f"Unauthorized delete by {request.user.email} to {admin.email}")
                    return Response({'error': 'No access'}, status=status.HTTP_403_FORBIDDEN)

            admin_email = admin.email
            admin.delete()
            logger.info(f"Admin {admin_email} deleted by {request.user.email}")
            return Response({'message': 'Admin deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting admin: {str(e)}")
            return Response({'error': 'Failed to delete admin'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)