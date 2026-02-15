from django.urls import path
from .views import (
    cart_detail,
    add_to_cart,
    remove_cart_item,
    update_cart_item,
    update_cart_item_size
)

urlpatterns = [
  


    path('', cart_detail, name='cart-detail'),
    path('add/', add_to_cart, name='add_to_cart'),

    # CART
    path('remove/<int:item_id>/', remove_cart_item),
    path('item/<int:item_id>/', update_cart_item, name='update_cart_item'),    # PATCH /api/cart/item/ID/
    path('item/<int:item_id>/size/', update_cart_item_size, name='update_cart_item_size'),


   
]
