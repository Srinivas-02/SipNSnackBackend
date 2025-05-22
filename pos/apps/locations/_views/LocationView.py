from django.http import JsonResponse
from rest_framework.views import APIView
import json
from django.core.exceptions import ObjectDoesNotExist
from pos.utils.logger import POSLogger
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.http import require_GET
from pos.apps.accounts.models import User
from pos.apps.locations.models import LocationModel

logger = POSLogger(__name__)

@require_GET
def get_location_names(request):
    """Get all location names and IDs accessible to the user"""
    try:
        user = request.user
        if user.is_super_admin:
            locations = LocationModel.objects.values('id', 'name')
        elif user.is_franchise_admin or user.is_staff_member:
            locations = user.locations.values('id', 'name')
        else:
            logger.warning(f"Unauthorized access attempt to location names by {user.email}")
            return JsonResponse({'error': 'Not authorized'}, status=403)
        logger.info(f"Location names accessed by {user.email}")
        return JsonResponse(list(locations), safe=False)
    except Exception as e:
        logger.error(f"Error retrieving location names: {str(e)}")
        return JsonResponse({'error': 'Error retrieving locations'}, status=500)

class LocationView(APIView):
    """
    Single endpoint for all operations:
    - GET: All locations or specific location (?id=) for authorized users
    - POST: Create location (Super Admin only)
    - PATCH: Update location (Super Admin or Franchise Admin for assigned locations)
    - DELETE: Delete specific location (Super Admin only)
    """
    
    def get(self, request):
        """Get all locations or specific one if ID provided"""
        location_id = request.GET.get('id')
        user = request.user

        if not (user.is_super_admin or user.is_franchise_admin or user.is_staff_member):
            logger.warning(f"Unauthorized access attempt by {user.email}")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        if location_id:
            try:
                location = LocationModel.objects.get(id=location_id)
                if user.is_super_admin:
                    pass  # Super Admin can access any location
                elif user.is_franchise_admin or user.is_staff_member:
                    if location.id not in [loc['id'] for loc in user.locations.values('id')]:
                        logger.warning(f"User {user.email} attempted to access unauthorized location {location_id}")
                        return Response({'error': 'You do not have access to this location'}, status=status.HTTP_403_FORBIDDEN)
                
                logger.info(f"Location {location.id} details accessed by {user.email}")
                return Response({
                    'id': location.id,
                    'name': location.name,
                    'address': location.address,
                    'city': location.city,
                    'state': location.state,
                    'phone': location.phone
                })
            except ObjectDoesNotExist:
                logger.warning(f"Attempt to access non-existent location {location_id} by {user.email}")
                return Response({'error': 'Location not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Super Admin: all locations
        if user.is_super_admin:
            locations = LocationModel.objects.values('id', 'name', 'city', 'state', 'address', 'phone')
        elif user.is_franchise_admin or user.is_staff_member:
            locations = user.locations.values('id', 'name', 'city', 'state', 'address', 'phone')
        else:
            logger.warning(f"Unauthorized access attempt by {user.email}")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        logger.info(f"Locations list accessed by {user.email}")
        return Response(list(locations))

    def post(self, request):
        """Create new location (Super Admin only)"""
        if not request.user.is_super_admin:
            logger.warning(f"Unauthorized create attempt by {request.user.email}")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        try:
            data = json.loads(request.body)
            location = LocationModel.objects.create(
                name=data.get('name', ''),
                address=data.get('address', ''),
                city=data.get('city', ''),
                state=data.get('state', ''),
                phone=data.get('phone', None)
            )
            logger.info(f"New location '{location.name}' created by {request.user.email}")
            return Response({'id': location.id, 'status': 'created'}, status=status.HTTP_201_CREATED)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in location creation request by {request.user.email}")
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating location: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """Update location (Super Admin or Franchise Admin for assigned locations)"""
        if not (request.user.is_super_admin or request.user.is_franchise_admin):
            logger.warning(f"Unauthorized update attempt by {request.user.email}")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        try:
            data = json.loads(request.body)
            if 'id' not in data:
                logger.warning(f"Location update attempt without ID by {request.user.email}")
                return Response({'error': 'Location ID required'}, status=status.HTTP_400_BAD_REQUEST)

            location = LocationModel.objects.get(id=data['id'])
            
            # Franchise Admin: Check location access
            if request.user.is_franchise_admin:
                if location.id not in [loc['id'] for loc in request.user.locations.values('id')]:
                    logger.warning(f"Franchise admin {request.user.email} attempted to update unauthorized location {data['id']}")
                    return Response({'error': 'You do not have access to this location'}, status=status.HTTP_403_FORBIDDEN)

            # Update only provided fields
            if 'name' in data:
                location.name = data['name']
            if 'address' in data:
                location.address = data['address']
            if 'city' in data:
                location.city = data['city']
            if 'state' in data:
                location.state = data['state']
            if 'phone' in data:
                location.phone = data['phone']
            
            location.save()
            logger.info(f"Location '{location.name}' updated by {request.user.email}")
            return Response({'status': 'updated'})
        except ObjectDoesNotExist:
            logger.warning(f"Attempt to update non-existent location {data.get('id')} by {request.user.email}")
            return Response({'error': 'Location not found'}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in location update request by {request.user.email}")
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating location: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete specific location (Super Admin only)"""
        if not request.user.is_super_admin:
            logger.warning(f"Unauthorized delete attempt by {request.user.email}")
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        location_id = request.GET.get('id')
        if not location_id:
            logger.warning(f"Delete attempt without ID by {request.user.email}")
            return Response({'error': 'Location ID required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            location = LocationModel.objects.get(id=location_id)
            location_name = location.name
            location.delete()
            logger.info(f"Location '{location_name}' deleted by {request.user.email}")
            return Response({'status': f'Location {location_id} deleted'})
        except ObjectDoesNotExist:
            logger.warning(f"Attempt to delete non-existent location {location_id} by {request.user.email}")
            return Response({'error': 'Location not found'}, status=status.HTTP_404_NOT_FOUND)