from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Address, UserProfile

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ("user",)

class MeProfileSerializer(serializers.Serializer):
    # User fields
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    # Profile fields
    screen_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    gender = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    dob = serializers.DateField(required=False, allow_null=True)

    def validate_phone(self, value):
        if value in (None, ""):
            return value
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("Phone must be 10 digits")
        return value

    def validate_gender(self, value):
        if value in (None, ""):
            return value
        if value not in ("Female", "Male"):
            raise serializers.ValidationError("Gender must be Female or Male")
        return value