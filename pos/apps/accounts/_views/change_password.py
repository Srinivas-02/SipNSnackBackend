from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status

class ChangePasswordView(APIView):
    def get(self, request):
        """Authenticate location"""
        
        return JsonResponse({
            'success': True,
            'location_id': 1
        })