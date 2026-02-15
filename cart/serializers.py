from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):
    size = serializers.SerializerMethodField()
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "size"]
    
    
    def get_size(self, obj):
        return obj.size.size if obj.size else None


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'items']

# class WishlistSerializer(serializers.ModelSerializer):
#     product = ProductSerializer(read_only=True)
#     class Meta:
#         model = Wishlist
#         fields = ['id', 'product']