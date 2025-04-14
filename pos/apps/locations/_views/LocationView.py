from django.http import JsonResponse
from rest_framework.views import APIView
import json
from django.core.exceptions import ObjectDoesNotExist
from pos.utils.permissions import IsSuperAdmin
from pos.utils.logger import POSLogger
from rest_framework.response import Response
from rest_framework import status

from pos.apps.locations.models import LocationModel

logger = POSLogger(__name__)

class LocationView(APIView):
    """
    Single endpoint for all operations:
    - GET: All locations (default) or specific location (?id=)
    - POST: Create location
    - PATCH: Update location
    - DELETE: Delete location
    
    Protected: Only super admins can access this view
    """
    permission_classes = [IsSuperAdmin]
    
    def get(self, request):
        """Get all locations or specific one if ID provided"""
        location_id = request.GET.get('id')
        
        if location_id:
            # Single location
            try:
                location = LocationModel.objects.get(id=location_id)
                logger.info(f"Location {location.id} details accessed by {request.user.email}")
                return JsonResponse({
                    'id': location.id,
                    'name': location.name,
                    'address': location.address,
                    'city': location.city,
                    'state': location.state,
                    'password': location.password
                })
            except ObjectDoesNotExist:
                logger.warning(f"Attempt to access non-existent location {location_id}")
                return JsonResponse({'error': 'Location not found'}, status=404)
        else:
            # All locations
            locations = list(LocationModel.objects.values(
                'id', 'name', 'city', 'state','password',
            ))
            logger.info(f"All locations list accessed by {request.user.email}")
            return JsonResponse(locations, safe=False)

    def post(self, request):
        """Create new location with optional fields"""
        try:
            data = json.loads(request.body)
            
            # Create with any provided fields
            location = LocationModel.objects.create(
                name=data.get('name', ''),
                address=data.get('address', ''),
                city=data.get('city', ''),
                state=data.get('state', ''),
                password=data.get('password', '')
            )
            logger.info(f"New location '{location.name}' created by {request.user.email}")
            return JsonResponse({'id': location.id, 'status': 'created'}, status=201)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in location creation request")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error creating location: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    def patch(self, request):
        """Update location with only provided fields"""
        try:
            data = json.loads(request.body)
            
            if 'id' not in data:
                logger.warning("Attempt to update location without providing ID")
                return JsonResponse({'error': 'Location ID required'}, status=400)

            try:
                location = LocationModel.objects.get(id=data['id'])
                
                # Update only provided fields
                if 'name' in data:
                    location.name = data['name']
                if 'address' in data:
                    location.address = data['address']
                if 'city' in data:
                    location.city = data['city']
                if 'state' in data:
                    location.state = data['state']
                if 'password' in data:
                    location.password = data['password']
                
                location.save()
                logger.info(f"Location '{location.name}' updated by {request.user.email}")
                return JsonResponse({'status': 'updated'})
            except ObjectDoesNotExist:
                logger.warning(f"Attempt to update non-existent location {data['id']}")
                return JsonResponse({'error': 'Location not found'}, status=404)
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON in location update request")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    def delete(self, request):
        """
        Delete locations:
        - If ID is provided: delete specific location
        - If no ID: delete all locations
        """
        location_id = request.GET.get('id')
        
        if location_id:
            # Delete specific location
            try:
                location = LocationModel.objects.get(id=location_id)
                location_name = location.name
                location.delete()
                logger.info(f"Location '{location_name}' deleted by {request.user.email}")
                return JsonResponse({'status': f'Location {location_id} deleted'})
            except ObjectDoesNotExist:
                logger.warning(f"Attempt to delete non-existent location {location_id}")
                return JsonResponse({'error': 'Location not found'}, status=404)
        else:
            # Delete all locations
            count, _ = LocationModel.objects.all().delete()
            logger.warning(f"All locations ({count}) deleted by {request.user.email}")
            return JsonResponse({'status': f'All locations deleted', 'count': count})