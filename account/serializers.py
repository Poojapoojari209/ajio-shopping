# account/serializers.py
from rest_framework import serializers
from users.models import Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id", "name", "mobile", "pincode", "area", "address_line",
            "landmark", "city", "state", "type", "is_default"
        ]
