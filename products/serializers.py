from rest_framework import serializers
from .models import (
    Product, Category, SubCategory, Brand,
    ProductImage, ProductSize, ProductVariant,
    VariantImage, Color
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = "__all__"


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "url"]

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return ""
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = "__all__"


# ----------------- COMMON MIXIN FOR IMAGE URLS -----------------
class AbsUrlMixin:
    def abs_url(self, request, path: str) -> str:
        if not path:
            return ""
        return request.build_absolute_uri(path) if request else path


# ----------------- PRODUCT LIST SERIALIZER -----------------
class ProductSerializer(serializers.ModelSerializer, AbsUrlMixin):
    brand = serializers.CharField(source="brand.name", read_only=True)
    image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()
    discount_percent = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "brand", "slug",
            "price", "discount_price", "discount_percent",
            "image", "images", "sizes"
        ]

    def get_image(self, obj):
        request = self.context.get("request")
        first = obj.images.first()
        if first and first.image:
            return self.abs_url(request, first.image.url)
        return ""

    def get_images(self, obj):
        request = self.context.get("request")
        out = []
        for img in obj.images.all():
            if img.image:
                out.append(self.abs_url(request, img.image.url))
        return out

    def get_sizes(self, obj):
        return [{"size": s.size, "stock": s.stock} for s in obj.sizes.all()]

    def get_discount_percent(self, obj):
        try:
            if obj.price and obj.discount_price and obj.discount_price > 0 and obj.discount_price < obj.price:
                return round(((obj.price - obj.discount_price) / obj.price) * 100, 0)
        except:
            pass
        return 0


# ----------------- VARIANTS -----------------
class VariantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantImage
        fields = ["image"]


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ["id", "name", "hex_code"]

class VariantImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = VariantImage
        fields = ["id", "url"]

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return ""
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class ProductVariantSerializer(serializers.ModelSerializer, AbsUrlMixin):
    color = ColorSerializer()
    images = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ["id", "color", "images"]

    def get_images(self, obj):
        # returns ["http://.../media/variant_images/..", ...]
        request = self.context.get("request")
        out = []
        for im in obj.images.all():
            if not im.image:
                continue
            url = im.image.url
            out.append(request.build_absolute_uri(url) if request else url)
        return out

# ----------------- PRODUCT DETAIL (FOR QUICK VIEW + PDP) -----------------
class ProductDetailSerializer(serializers.ModelSerializer, AbsUrlMixin):
    brand = serializers.CharField(source="brand.name", read_only=True)

    # ADD THESE FOR QUICK VIEW
    image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()

    variants = ProductVariantSerializer(many=True, read_only=True)
    base_color = ColorSerializer()

    class Meta:
        model = Product
        fields = [
            "id", "name", "brand",
            "price", "discount_price",
            "color_name", "base_color",
            "image", "images", "sizes",
            "variants"
        ]

    def get_image(self, obj):
        request = self.context.get("request")
        first = obj.images.first()
        if first and first.image:
            return self.abs_url(request, first.image.url)
        return ""

    def get_images(self, obj):
        request = self.context.get("request")
        out = []
        for im in obj.images.all():
            if not im.image:
                continue
            url = im.image.url
            out.append(request.build_absolute_uri(url) if request else url)
        return out
    
    def get_sizes(self, obj):
        return [{"size": s.size, "stock": s.stock} for s in obj.sizes.all()]
