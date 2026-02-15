# account/urls.py
from django.urls import path
from . import views

urlpatterns = [
   
    # JWT APIs
    path("api/addresses/", views.address_list_api, name="api_address_list"),
    path("api/addresses/create/", views.address_create_api, name="api_address_create"),
    path("api/addresses/<int:pk>/update/", views.address_update_api, name="api_address_update"),
    path("api/addresses/<int:pk>/delete/", views.address_delete_api, name="api_address_delete"),
    path("api/addresses/<int:pk>/default/", views.address_set_default_api, name="api_address_default"),
]
