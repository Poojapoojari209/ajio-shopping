from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Gender)
admin.site.register(Category)  # products
admin.site.register(SubCategory)
admin.site.register(Brand)


#  Show ProductImage + ProductSize inside Product page
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 4 #shows 4 rows (front/back/side/zoom)

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1

class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 4
    min_num = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    show_change_link = True


# ---------------- PRODUCT ADMIN ----------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "base_color", "price", "discount_price", "category", "subcategory")
    list_filter = ("brand", "base_color")
    search_fields = ("name", "brand__name")
    prepopulated_fields = {"slug": ("name",)}

    inlines = [
        ProductImageInline,
        ProductSizeInline,
        ProductVariantInline,  
    ]


# ---------------- VARIANT ADMIN ----------------

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "color")
    list_filter = ("color", "product")
    search_fields = ("product__name", "color__name")

    inlines = [VariantImageInline]  # Images under variant


# ---------------- COLOR ADMIN ----------------

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "hex_code")
    search_fields = ("name",)


# admin.site.register(ProductImage)
# admin.site.register(ProductSize)
# admin.site.register(VariantImage)
admin.site.register(ServiceablePincode)
admin.site.register(ProductPincodeAvailability)