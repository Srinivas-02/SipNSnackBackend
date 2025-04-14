from django.urls import path
from ._views.MenuItems import MenuItems

urlpatterns = [
   
path('menu-items/', MenuItems.as_view()),    
    
]