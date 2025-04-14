from django.http import JsonResponse
from rest_framework.views import APIView
import json
from django.core.exceptions import ObjectDoesNotExist

from pos.apps.locations.models import LocationModel

class LocationView(APIView):
    """
    Single endpoint for all operations:
    - GET: All locations (default) or specific location (?id=)
    - POST: Create location
    - PATCH: Update location
    - DELETE: Delete location
    """
    
    def get(self, request):
        """Get all locations or specific one if ID provided"""
        location_id = request.GET.get('id')
        
        if location_id:
            # Single location
            try:
                location = LocationModel.objects.get(id=location_id)
                return JsonResponse({
                    'id': location.id,
                    'name': location.name,
                    'address': location.address,
                    'city': location.city,
                    'state': location.state,
                    'password': location.password
                })
            except ObjectDoesNotExist:
                return JsonResponse({'error': 'Location not found'}, status=404)
        else:
            # All locations
            locations = list(LocationModel.objects.values(
                'id', 'name', 'city', 'state','password',
            ))
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
            return JsonResponse({'id': location.id, 'status': 'created'}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def patch(self, request):
        """Update location with only provided fields"""
        try:
            data = json.loads(request.body)
            
            if 'id' not in data:
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
                if 'location_password' in data:
                    location.password = data['password']
                
                location.save()
                return JsonResponse({'status': 'updated'})
            except ObjectDoesNotExist:
                return JsonResponse({'error': 'Location not found'}, status=404)
                
        except json.JSONDecodeError:
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
                location.delete()
                return JsonResponse({'status': f'Location {location_id} deleted'})
            except ObjectDoesNotExist:
                return JsonResponse({'error': 'Location not found'}, status=404)
        else:
            # Delete all locations
            count, _ = LocationModel.objects.all().delete()
            return JsonResponse({'status': f'All locations deleted', 'count': count})