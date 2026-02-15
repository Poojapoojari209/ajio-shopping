from django.db import models
from django.utils.text import slugify

class Gender(models.Model):
    name = models.CharField(max_length=50)   # Men, Women, Kids
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.gender} - {self.name}"


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    # AJIO ORIGINAL COLOR
    base_color = models.ForeignKey(
        "Color",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="base_products"
    )
    color_name = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return f"{self.product.name} - Image{self.id}"


class ProductSize(models.Model):
    SIZE_CHOICES = [
        # Cloth
        ("XS", "XS"), ("S", "S"), ("M", "M"),
        ("L", "L"), ("XL", "XL"), ("XXL", "XXL"),
        ("28", "28"), ("30", "30"), ("32", "32"), ("34", "34"), ("36", "36"),

        # Shoes
        ("5", "5"), ("6", "6"), ("7", "7"),
        ("8", "8"), ("9", "9"), ("10", "10"),
        ("11", "11"), ("12", "12"),

        # Kids Age
        ("0-2", "0-2 Years"),
        ("3-5", "3-5 Years"),
        ("6-7", "6-7 Years"),
        ("8-10", "8-10 Years"),
        ("11-14", "11-14 Years"),

         # Free Size
        ("FZ", "Free Size"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="sizes"
    )
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("product", "size")  # prevents duplicate size for same product

    def __str__(self):
        return f"{self.product.name} - {self.size} ({self.stock})"


# product color variant
class Color(models.Model):
    name = models.CharField(max_length=50)              # e.g. "Ice-Blue"
    hex_code = models.CharField(max_length=7, blank=True, null=True)  # e.g. "#A9B7D0"

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="variants")
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name="variants")

   
    def __str__(self):
        return f"{self.product.name} - {self.color.name}"


class VariantImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="variant_images/")

    def __str__(self):
        return f"Image for {self.variant}"
    

class ServiceablePincode(models.Model):
    pincode = models.CharField(max_length=6, unique=True)
    city = models.CharField(max_length=80, blank=True, null=True)
    state = models.CharField(max_length=80, blank=True, null=True)
    


    def __str__(self):
        return self.pincode

# Product availability by pincode (AJIO-like)
class ProductPincodeAvailability(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="pincode_availability")
    pincode = models.ForeignKey(ServiceablePincode, on_delete=models.CASCADE, related_name="product_availability")

    # optional but very useful
    is_available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)   # stock for this pincode
    cod_available = models.BooleanField(default=True)
    eta_days = models.PositiveIntegerField(default=3)

    class Meta:
        unique_together = ("product", "pincode")

    def __str__(self):
        return f"{self.product.name} @ {self.pincode.pincode} ({'Yes' if self.is_available else 'No'})"
