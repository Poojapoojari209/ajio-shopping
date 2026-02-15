from rest_framework import serializers
from .models import Order, OrderItem, Payment,  ProductRating, OrderStatusHistory
from users.models import Address
import re

class AddressMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id","name","mobile","type","address_line","area","landmark","city","state","pincode","is_default"]

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ("status", "status_label", "note", "created_at")


class OrderItemSerializer(serializers.ModelSerializer):
    product_image = serializers.SerializerMethodField()
    product_name = serializers.CharField(source="product.name", read_only=True)
    is_rated = serializers.SerializerMethodField()
    rating_value = serializers.SerializerMethodField()  # 1..5 or None

    # size = serializers.CharField(read_only=True, allow_blank=True)
    size = serializers.SerializerMethodField()


    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "product_image", "quantity", "price", "size", "is_rated", "rating_value",]

    def get_product_image(self, obj):
        request = self.context.get("request")

        image = obj.product.images.first()
        if image and image.image:
            if request:
                return request.build_absolute_uri(image.image.url)
            return image.image.url

        return None
    
    
    def get_is_rated(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return ProductRating.objects.filter(order_item=obj, user=request.user).exists()

    def get_rating_value(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        r = ProductRating.objects.filter(order_item=obj, user=request.user).first()
        return r.rating if r else None
    
    def get_size(self, obj):
        """
        Returns ONLY size like: XS / S / M / XL / 32 / UK 7
        Removes: product name, '-', '(8)' etc if accidentally stored.
        """
        raw = (obj.size or "").strip()
        if not raw:
            return ""

        # If stored like "Men Jogger - 32 (8)" -> take last part after "-"
        if "-" in raw:
            raw = raw.split("-")[-1].strip()

        # Remove "(8)" or any bracketed text
        raw = re.sub(r"\s*\(.*?\)\s*", "", raw).strip()

        return raw
        
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    address = AddressMiniSerializer(read_only=True)
    formatted_order_id = serializers.SerializerMethodField()

    status_label = serializers.CharField(source="get_status_display", read_only=True)

    status_history = OrderStatusHistorySerializer(many=True, read_only=True)


    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "formatted_order_id",
            "status",
            "status_label",
            "created_at",
            "total_amount",
            "items",
            "address",
            "status_history",
        ]

    def get_formatted_order_id(self, obj):
        return "FN" + str(obj.id).zfill(10)

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
