from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from pos.apps.locations.models import LocationModel as Location
from pos.utils.logger import POSLogger
User = get_user_model()

class LoginView(APIView):
    LOG = POSLogger()
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def post(self, request):
        login_type = request.data.get('login_type')  
        self.LOG.info(f"Login type received: {login_type}")  # Debug print for login type
        if login_type == 'location':
            return self.verify_location(
                request.data.get('location_name'),
                request.data.get('location_password')
            )
        elif login_type == 'user':
            return self.authenticate_user(
                request.data.get('email'),
                request.data.get('password')
            )
        else:
            return JsonResponse(
                {'error': 'Invalid login_type. Must be "user" or "location"'},
                status=400
            )

    def verify_location(self, location_name, location_password):
        if not location_name or not location_password:
            return JsonResponse(
                {'error': 'Both location_name and location_password are required'},
                status=400
            )

        try:
            location = Location.objects.get(name=location_name, is_active=True)
        except Location.DoesNotExist:
            return JsonResponse(
                {'error': 'Location not found'},
                status=404
            )

        if location.password != location_password:
            return JsonResponse(
                {'error': 'Invalid location password'},
                status=401
            )

        return JsonResponse(
            {
                'status': 'success',
                'message': 'Location verified',
                'location_id': location.id,
                'location_name': location.name
            },
            status=200
        )

    def authenticate_user(self, email, password):
        if not email or not password:
            return JsonResponse(
                {'error': 'Both email and password are required'},
                status=400
            )

        user = authenticate(username=email, password=password)
        
        if not user:
            return JsonResponse(
                {'error': 'Invalid credentials'},
                status=401
            )

        if user.is_super_admin:
            role = 'super_admin'
        elif user.is_franchise_admin:
            role = 'franchise_admin'
        elif user.is_staff_member:
            role = 'staff'
        else:
            return JsonResponse(
                {'error': 'User has no valid role'},
                status=403
            )

        response_data = {
            'message': 'Login successful',
            'id': user.id,
            'email': user.email,
            'role': role,
            'is_active': user.is_active
        }

        if role == 'super_admin':
            response_data['permissions'] = ['*']
        elif role == 'franchise_admin':
            response_data['managed_locations'] = list(
                user.locations.values('id', 'name', 'city')
            )
        elif role == 'staff':
            response_data['allowed_locations'] = list(
                user.locations.values('id', 'name')
            )

        return JsonResponse(response_data, status=200)