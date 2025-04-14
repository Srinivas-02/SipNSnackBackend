from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status

class LogoutView(APIView):
    def get(self, request):
        """Logout """
        
        return JsonResponse({
            'success': True,
            'location_id': 2
        })