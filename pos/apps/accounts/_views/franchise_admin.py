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
    - POST: Create franchise admin
    - GET: List all franchise admins or get specific one
    - PATCH: Update franchise admin
    - DELETE: Deactivate franchise admin
    
    Protected: Only super admins can access this view
    """
    
    def post(self, request):
        """Create new franchise admin"""
        required_fields = ['email', 'first_name', 'last_name', 'location_ids']
        if missing := [f for f in required_fields if f not in request.data]:
            logger.warning(f"Attempt to create franchise admin with missing fields: {missing}")
            return Response(
                {'error': f'Missing fields: {", ".join(missing)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.user.is_super_admin:
            try:
                franchise_admin = User.objects.create_user(
                    email=request.data['email'],
                    first_name=request.data['first_name'],
                    last_name=request.data['last_name'],
                    is_franchise_admin=True
                )

                # Ensure no password login is possible
                franchise_admin.set_unusable_password()
                franchise_admin.save()

                if 'location_ids' in request.data:
                    locations = LocationModel.objects.filter(id__in=request.data['location_ids'])
                    franchise_admin.locations.set(locations)

                logger.info(f"Franchise admin {franchise_admin.email} created by {request.user.email}")
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
        elif request.user.is_franchise_admin:
            admin = get_object_or_404(User,id=request.user.id, is_franchise_admin = True)
            locations = list(admin.locations.values('id'))
            requested_locations = request.data['location_ids']
            admin_locations = [loc['id'] for loc in locations]
            # Check if all requested locations are in admin's accessible locations
            if not all(loc_id in admin_locations for loc_id in requested_locations):
                logger.warning(f"Franchise admin {request.user.email} attempted to create admin with unauthorized locations")
                return Response(
                    {'error': 'You do not have access to all requested locations'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                franchise_admin = User.objects.create_user(
                    email=request.data['email'],
                    first_name=request.data['first_name'],
                    last_name=request.data['last_name'],
                    is_franchise_admin=True
                )

                # Ensure no password login is possible
                franchise_admin.set_unusable_password()
                franchise_admin.save()

                locations = LocationModel.objects.filter(id__in=requested_locations)
                franchise_admin.locations.set(locations)

                logger.info(f"Franchise admin {franchise_admin.email} created by {request.user.email}")
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
        else:
            return(Response({'error':'not allowed'}))

    def get(self, request):
        """Get all franchise admins or specific one"""
        
        admin_id = request.query_params.get('id')
        if admin_id:
            try:
                admin = get_object_or_404(User, id=admin_id, is_franchise_admin=True)
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
                
                # Prepare response with locations as arrays
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
                
                logger.info(f"All franchise admins list accessed by {request.user.email}")
                return Response(admins_data)
            elif request.user.is_franchise_admin:
                admin = get_object_or_404(User, id=request.user.id, is_franchise_admin=True)
                
                # Get all franchise admins that have access to any of these locations
                franchise_admins = User.objects.filter(
                    is_franchise_admin=True,
                    locations__in=admin.locations.all()
                ).distinct()
                
                # Prepare response with locations as arrays
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
                return Response({'error' : 'not allowed'})


    def patch(self, request):
        """Update franchise admin details"""
        logger.info("Franchise admin update request received")

        if 'id' not in request.data:
            logger.warning("Attempt to update franchise admin without providing ID")
            return Response({'error': 'Franchise admin ID required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            admin = get_object_or_404(User, id=request.data['id'], is_franchise_admin=True)

            if request.user.is_super_admin:
                # Super admin can update freely
                pass
            elif request.user.is_franchise_admin:
                # Franchise admin can only update if target admin is within their locations
                requestor_locations = set(request.user.locations.values_list('id', flat=True))
                target_locations = set(admin.locations.values_list('id', flat=True))
                if not target_locations.issubset(requestor_locations):
                    logger.warning(f"{request.user.email} unauthorized to update this admin")
                    return Response({'error': 'Unauthorized to update this franchise admin'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

            # Perform updates
            for field in ['first_name', 'last_name', 'email']:
                if field in request.data:
                    setattr(admin, field, request.data[field])

            if 'location_ids' in request.data:
                location_ids = request.data['location_ids']
                new_locations = LocationModel.objects.filter(id__in=location_ids)

                if request.user.is_franchise_admin:
                    if not set(location_ids).issubset(request.user.locations.values_list('id', flat=True)):
                        return Response({'error': 'Cannot assign unauthorized locations'}, status=status.HTTP_403_FORBIDDEN)

                admin.locations.set(new_locations)

            admin.save()
            logger.info(f"Franchise admin {admin.email} updated by {request.user.email}")
            return Response({'message': 'Franchise admin updated'})

        except Exception as e:
            logger.error(f"Error updating franchise admin: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)


    def delete(self, request):
        """Permanently delete franchise admin from database"""
        logger.info("Franchise admin delete request received")

        if 'id' not in request.query_params:
            logger.warning("Attempt to delete franchise admin without providing ID")
            return Response({'error': 'Specify ?id=<franchise_admin_id>'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            admin = get_object_or_404(User, id=request.query_params['id'], is_franchise_admin=True)

            if request.user.is_super_admin:
                pass  # Full access
            elif request.user.is_franchise_admin:
                requestor_locations = set(request.user.locations.values_list('id', flat=True))
                target_locations = set(admin.locations.values_list('id', flat=True))
                if not target_locations.issubset(requestor_locations):
                    logger.warning(f"{request.user.email} unauthorized to delete this admin")
                    return Response({'error': 'Unauthorized to delete this franchise admin'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

            admin_email = admin.email
            admin.delete()
            logger.warning(f"Franchise admin {admin_email} deleted by {request.user.email}")
            return Response({'message': 'Franchise admin permanently deleted'}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error deleting franchise admin: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

