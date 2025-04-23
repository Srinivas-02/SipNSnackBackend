from django.urls import path
from .views import OrderView, OrderReceiptView

urlpatterns = [
   
    path('create-order/', OrderView.as_view()),
    path('generate-order-receipt/<int:order_id>/', OrderReceiptView.as_view()),

]