from rest_framework.views import APIView
from django.http import JsonResponse

class MenuItems(APIView):
    def get(self, request):
        return JsonResponse({
            'success': True,
            'menu_items': []
        })