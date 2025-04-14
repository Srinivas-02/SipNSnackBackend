from django.urls import path

from pos.apps.locations._views.LocationView import LocationView


urlpatterns = [
    path('', LocationView.as_view(), name='locations'),
]