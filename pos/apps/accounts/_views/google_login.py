from django.conf import settings
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()

class GoogleLoginView(APIView):
    """
    POST endpoint to handle Google Sign-In.
    Expects a JSON body with a 'token' field containing the Google ID token.
    """
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'No token provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the token with Google's OAuth2 API
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            # Verify issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid token issuer.')

            # Ensure email is verified
            if not idinfo.get('email_verified', False):
                return Response({'error': 'Google account email not verified.'}, status=status.HTTP_400_BAD_REQUEST)

            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            domain = email.split('@')[-1].lower()

            if domain != 'sn15.ai':
                return Response({
                    'error': "Your account is not authorized to sign in ."
                }, status=status.HTTP_403_FORBIDDEN)
            
            defaults = {
                'first_name': first_name,
                'last_name': last_name,
                'is_franchise_admin': True,
            }

            # Get or create the user (preserves existing flags)
            user, created = User.objects.get_or_create(
                email=email,
                defaults=defaults
            )

            # Issue our own JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return Response({
                'access': access_token,
                'refresh': refresh_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_franchise_admin': user.is_franchise_admin,
                    'is_super_admin': user.is_super_admin,
                    'is_staff_member': user.is_staff_member,
                }
            })

        except ValueError:
            return Response({'error': 'Invalid Google token.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
