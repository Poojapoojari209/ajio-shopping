"""
URL configuration for ajio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from .views import index
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
      # HOME
    path('admin/', admin.site.urls),
    path('', index, name='index'),
  

    # API
    path('api/cart/', include('cart.urls')),
    path('api/users/', include('users.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/products/', include('products.urls')),
    
    path("cart/", views.cart_page, name="cart"),
    path("wishlist/", views.wishlist_page, name="wishlist"),
    
    # AUTH PAGES 
    path('login/', lambda request: render(request, 'login.html'), name="login"),
    path('register/', lambda request: render(request, 'register.html'), name="register"),

    #  ORDER PAGES (MUST BE BEFORE products include)
    path("orders/confirm/<int:order_id>/", views.order_confirm_page, name="order_confirm"),
    path("orders/success/<int:order_id>/", views.order_success_page, name="order_success"),


    #  accounts

    path('account/orders/', views.orders, name='account-orders'),
    path('account/wallet/', views.wallet, name='account-wallet'),
    path('account/profile/', views.profile, name='account-profile'),
    path('account/address_book/', views.address_book, name='account-address_book'),
    path('account/payments/', views.payments, name='account-payments'),
    path('account/invites/', views.invites, name='account-invites'),

  

    # order detail 
    path("account/orders/<int:order_id>/", views.order_detail_page, name="account-order-detail"),


    path("customer-care/", views.customer_care_page, name="customer_care"),
    # API for customer-care orders carousel
    path("api/customer-care/orders/", views.customer_care_orders_api, name="customer_care_orders_api"),





    # Category pages LAST
    path('', include('products.urls')),


    path("", include("account.urls")),
   
]

# if settings.DEBUG:
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

