from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from pos.apps.locations.models import LocationModel as Location
from pos.utils.logger import POSLogger
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()

logger = POSLogger(__name__)

class LoginView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def get_tokens_for_user(self, user):
        """Generate JWT tokens for the user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def verify_location(self, location_name, location_password):
        """Verify location credentials"""
        # TODO: Implement location verification
        logger.warning("Location login not implemented yet")
        return JsonResponse(
            {'error': 'Location login not implemented'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

    def authenticate_user(self, email, password):
        """Authenticate user and return tokens"""
        if not email or not password:
            logger.error("Missing credentials in login request")
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        user = authenticate(username=email, password=password)
        
        if not user:
            logger.warning(f"Failed login attempt for email: {email}")
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate tokens
        tokens = self.get_tokens_for_user(user)
        
        # Determine user role
        user_role = 'user'
        if user.is_super_admin:
            user_role = 'super_admin'
        elif user.is_franchise_admin:
            user_role = 'admin'
        elif user.is_staff_member:
            user_role = 'staff'
        
        # Add user info to response
        response_data = {
            **tokens,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user_role,
                'is_super_admin': user.is_super_admin,
                'is_franchise_admin': user.is_franchise_admin,
                'is_staff_member': user.is_staff_member,
                'is_active': user.is_active
            }
        }
        
        logger.info(f"Successful login for user: {user.email}")
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        """Handle login requests"""
        login_type = request.data.get('login_type')
        logger.debug(f"Login attempt with type: {login_type}")

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
            logger.error(f"Invalid login type: {login_type}")
            return Response(
                {'error': 'Invalid login_type. Must be "user" or "location"'},
                status=status.HTTP_400_BAD_REQUEST
            )