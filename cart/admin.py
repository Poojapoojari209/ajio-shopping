from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Cart)      # cart
admin.site.register(CartItem)
# admin.site.register(Wishlist)