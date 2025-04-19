from django.urls import path
from .views import MenuItemsView, CategoryView

urlpatterns = [
   
path('menu-items/', MenuItemsView.as_view()),
path('categories/', CategoryView.as_view()), 
    
]