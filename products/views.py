from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from decimal import Decimal
from django.db.models import F, ExpressionWrapper, DecimalField, Q, Count, Case, When, Value
from django.shortcuts import get_object_or_404, render
from .models import *
from .serializers import *
from django.db.models.functions import Coalesce
from .models import Gender, Category, SubCategory, Product, ProductSize
from users.models import Address

# filter
def _get_selected_list(request, key):
    return [v for v in request.GET.getlist(key) if v]

@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail_api(request, pk):
    product = get_object_or_404(
        Product.objects.prefetch_related("images", "variants__color", "variants__images"),
        pk=pk
    )
    serializer = ProductDetailSerializer(product, context={"request": request})
    return Response(serializer.data)


# ---------------- API: PRODUCT LIST (SEARCH/FILTER/SORT) ----------------
@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    products = Product.objects.all()

    search = request.GET.get("search")
    subcategory = request.GET.get("subcategory")
    sort = request.GET.get("sort")
    max_price = request.GET.get("max_price")
    offer = request.GET.get("offer")
    min_offer = request.GET.get("min_offer")
    max_offer = request.GET.get("max_offer")
    
     # BRAND FILTER (NEW)
    brand_slugs = request.GET.getlist("brand")  # ?brand=shein&brand=gap

    
    # ---------- SEARCH ----------
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(brand__name__icontains=search) |
            Q(category__name__icontains=search) |
            Q(subcategory__name__icontains=search)
        )

    # ---------- SUBCATEGORY ----------
    if subcategory:
        products = products.filter(subcategory__slug=subcategory)

    # ---------- BRAND ----------
    if brand_slugs:
        products = products.filter(brand__slug__in=brand_slugs)


     # Discount percent calculation (database level)
    discount_percent_expr = ExpressionWrapper(
        (F("price") - F("discount_price")) * Decimal("100.0") / F("price"),
        output_field=DecimalField(max_digits=6, decimal_places=2)
    )

    # ---------- DISCOUNT ----------
    if offer and not min_offer:
        min_offer = offer


    #  Apply discount filters only when needed
    if min_offer or max_offer:
        products = products.filter(
            price__gt=0,
            discount_price__isnull=False,
            discount_price__gt=0,
            discount_price__lt=F("price")
        ).annotate(discount_percent=discount_percent_expr)

        if min_offer:
            products = products.filter(discount_percent__gte=Decimal(min_offer))

        if max_offer:
            products = products.filter(discount_percent__lte=Decimal(max_offer))

    # Max price filter (AJIO under price)
    if max_price:
        products = products.filter(discount_price__lte=Decimal(max_price))

    #  Sort
    if sort == "low":
        products = products.order_by("discount_price", "id")
    elif sort == "high":
        products = products.order_by("-discount_price", "-id")
    else:
        products = products.order_by("-id")

    serializer = ProductSerializer(products, many=True, context={"request": request})
    return Response(serializer.data)

# /Product Brand
@api_view(['GET'])
@permission_classes([AllowAny])
def brand_list(request):
    brands = Brand.objects.all()
    serializer = BrandSerializer(brands, many=True)
    return Response(serializer.data)

# Product Category list
@api_view(['GET'])
def category_list(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)

# PRODUCT DETAIL BY ID
# @api_view(['GET'])
# def product_detail(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     serializer = ProductSerializer(product)
#     return Response(serializer.data)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    similar_products = (
        Product.objects
        .filter(brand=product.brand, subcategory=product.subcategory)
        .exclude(id=product.id)
        .prefetch_related("images")
        .order_by("-id")[:12]
    )

    # --------------------------
    # Default pincode (your code)
    # --------------------------
    default_pin = ""
    if request.user.is_authenticated:
        addr = Address.objects.filter(user=request.user, is_default=True).first()
        if addr and addr.pincode:
            default_pin = addr.pincode

    SIZE_ORDER = [
        "XS", "S", "M", "L", "XL", "XXL", "FZ",
        "28", "30", "32", "34", "36",
        "5", "6", "7", "8", "9", "10", "11", "12",
        "0-2", "3-5", "6-7", "8-10", "11-14",
    ]

    sizes_qs = list(product.sizes.all())
    sizes_map = {s.size: s for s in sizes_qs}

    ordered_sizes = [sizes_map[k] for k in SIZE_ORDER if k in sizes_map]
    # add any leftover sizes not in list
    ordered_sizes += [s for s in sizes_qs if s.size not in SIZE_ORDER]


    context = {
        "product": product,
        "similar_products": similar_products,
        "default_pin": default_pin,
        "ordered_sizes": ordered_sizes, 
    }
    return render(request, "product_detail.html", context)

def category_products(request, gender, subcategory, category=None):
    # -----------------------------
    # Resolve URL objects
    # -----------------------------
    g = get_object_or_404(Gender, slug=gender)

    if category:
        cat = get_object_or_404(Category, slug=category, gender=g)
        subcat = get_object_or_404(SubCategory, slug=subcategory, category=cat)
    else:
        subcat = get_object_or_404(SubCategory, slug=subcategory, category__gender=g)
        cat = subcat.category

    # -----------------------------
    # Detect ProductSize relation automatically (Product -> ProductSize)
    # This is what you have in admin "PRODUCT SIZES"
  
    size_rel = None        # reverse accessor name (ex: "product_sizes" or "productsize_set")
    size_field = None      # field storing size value (ex: "size")
    stock_field = None     # field storing stock (ex: "stock")

    for rel in Product._meta.related_objects:
        rm = rel.related_model
        # match common model names
        if rm.__name__.lower() in ["productsize", "productsizes", "product_size", "product_sizes"]:
            size_rel = rel.get_accessor_name()
            fields = {f.name for f in rm._meta.get_fields()}
            for cand in ["size", "value", "label"]:
                if cand in fields:
                    size_field = cand
                    break
            for cand in ["stock", "qty", "quantity"]:
                if cand in fields:
                    stock_field = cand
                    break
            break

    # -----------------------------
    # Detect Variant relation ONLY for Colors (optional)
    # because your API uses variants__color
    # -----------------------------
    variant_rel = None
    for relname in ["variants", "variant_set", "productvariant_set"]:
        try:
            Product._meta.get_field(relname)
            variant_rel = relname
            break
        except Exception:
            continue

    color_lookup = None
    if variant_rel:
        variant_model = Product._meta.get_field(variant_rel).related_model
        variant_fields = {f.name for f in variant_model._meta.get_fields()}
        # if FK color exists, use name
        if "color" in variant_fields:
            color_lookup = f"{variant_rel}__color__name"
        elif "color_name" in variant_fields:
            color_lookup = f"{variant_rel}__color_name"

    # -----------------------------
    # Base queryset (subcategory products)
    # -----------------------------
    products = (
        Product.objects
        .filter(subcategory=subcat)
        .select_related("brand", "category", "subcategory")
        .prefetch_related("images")
        .distinct()
    )

    # prefetch sizes table if exists
    if size_rel:
        products = products.prefetch_related(size_rel)

    # prefetch variants for color if exists
    if variant_rel:
        products = products.prefetch_related(variant_rel, f"{variant_rel}__color")

    # -----------------------------
    # READ FILTER PARAMS (GET)
    # -----------------------------
    sort = request.GET.get("sort")  # low / high / default
    search = (request.GET.get("search") or "").strip()
    offer = (request.GET.get("offer") or "").strip().lower()

    max_price = request.GET.get("max_price")
    min_offer = request.GET.get("min_offer")
    max_offer = request.GET.get("max_offer")

    brand_slugs = request.GET.getlist("brand")
    colors = request.GET.getlist("color")
    sizes = request.GET.getlist("size")


    # /men/clothing/jeans/?offer=under999
    if offer == "under999":
        max_price = max_price or "999"
    elif offer == "under1499":
        max_price = max_price or "1499"
    elif offer == "min30":
        min_offer = min_offer or "30"
    elif offer == "min40":
        min_offer = min_offer or "40"
    elif offer == "min50":
        min_offer = min_offer or "50"
    # brand-xxx example: offer=brand-nike
    elif offer.startswith("brand-") and not brand_slugs:
        brand_slugs = [offer.replace("brand-", "", 1)]

    # -----------------------------
    # APPLY FILTERS
    # -----------------------------
    if search:
        products = products.filter(name__icontains=search)


    if brand_slugs:
        products = products.filter(brand__slug__in=brand_slugs)

    # color filter: Product.color OR variant color
    if colors:
        if hasattr(Product, "color"):
            # if Product.color is FK
            products = products.filter(color__name__in=colors)
        elif color_lookup:
            products = products.filter(**{f"{color_lookup}__in": colors}).distinct()
        # else ignore

    # size filter: from ProductSize table (NOT variants)
    if sizes and size_rel and size_field:
        products = products.filter(**{f"{size_rel}__{size_field}__in": sizes}).distinct()

    # discount percent
    discount_percent_expr = ExpressionWrapper(
        (F("price") - F("discount_price")) * Decimal("100.0") / F("price"),
        output_field=DecimalField(max_digits=6, decimal_places=2)
    )

    # ALWAYS annotate off_percent so template can use it anytime
    products = products.annotate(
        off_percent=Case(
            When(
                price__gt=0,
                discount_price__isnull=False,
                discount_price__gt=0,
                discount_price__lt=F("price"),
                then=discount_percent_expr
            ),
            default=Value(0),
            output_field=DecimalField(max_digits=6, decimal_places=2),
        )
    )
    

    if min_offer or max_offer:
        products = (
            products.filter(
                price__gt=0,
                discount_price__isnull=False,
                discount_price__gt=0,
                discount_price__lt=F("price")
            )
            .annotate(discount_percent=discount_percent_expr)
        )
        if min_offer:
            products = products.filter(discount_percent__gte=Decimal(min_offer))
        if max_offer:
            products = products.filter(discount_percent__lte=Decimal(max_offer))

    # max price using payable price
    if max_price:
        try:
            mx = Decimal(max_price)
            products = products.annotate(
                payable_price=Coalesce("discount_price", "price")
            ).filter(payable_price__lte=mx)
        except Exception:
            pass

    # sorting
    if sort == "low":
        products = products.annotate(
            payable_price=Coalesce("discount_price", "price")
        ).order_by("payable_price", "id")
    elif sort == "high":
        products = products.annotate(
            payable_price=Coalesce("discount_price", "price")
        ).order_by("-payable_price", "-id")
    else:
        products = products.order_by("-id")

    # -----------------------------
    # FACETS (sidebar counts)
    # build from category scope (AJIO style)
    # -----------------------------
    base = (
        Product.objects
        .filter(category=cat)
        .select_related("brand")
        .distinct()
    )

    if size_rel:
        base = base.prefetch_related(size_rel)
    if variant_rel:
        base = base.prefetch_related(variant_rel)

    subcat_facets = (
        SubCategory.objects
        .filter(category=cat)
        .annotate(cnt=Count("product"))
        .values("name", "slug", "cnt")
        .order_by("name")
    )

    brand_facets = (
        base.values("brand__name", "brand__slug")
        .annotate(cnt=Count("id", distinct=True))
        .order_by("brand__name")
    )

    # color facets
    if hasattr(Product, "color"):
        color_facets = (
            base.values(value=F("color__name"))
            .exclude(value__isnull=True)
            .exclude(value__exact="")
            .annotate(cnt=Count("id", distinct=True))
            .order_by("value")
        )
    elif color_lookup:
        color_facets = (
            base.values(value=F(color_lookup))
            .exclude(value__isnull=True)
            .exclude(value__exact="")
            .annotate(cnt=Count("id", distinct=True))
            .order_by("value")
        )
    else:
        color_facets = []

    # size facets from ProductSize table
    if size_rel and size_field:
        size_facets = (
            base.values(value=F(f"{size_rel}__{size_field}"))
            .exclude(value__isnull=True)
            .exclude(value__exact="")
            .annotate(cnt=Count("id", distinct=True))
            .order_by("value")
        )
    else:
        size_facets = []

    price_buckets = [
        {"label": "Below Rs.999", "value": "999"},
        {"label": "Rs.1000-1499", "value": "1499"},
        {"label": "Rs.1500-1999", "value": "1999"},
        {"label": "Rs.2000-2499", "value": "2499"},
    ]

    discount_buckets = [
        {"label": "30% and above", "value": "30"},
        {"label": "40% and above", "value": "40"},
        {"label": "50% and above", "value": "50"},
    ]

    return render(request, "products/category_products.html", {
        "gender": g,
        "category": cat,
        "subcategory": subcat,
        "products": products,

        "subcat_facets": subcat_facets,
        "brand_facets": brand_facets,
        "color_facets": color_facets,
        "size_facets": size_facets,
        "price_buckets": price_buckets,
        "discount_buckets": discount_buckets,

        "sel_gender": g.slug,
        "sel_subcat": subcat.slug,
        "sel_brands": set(brand_slugs),
        "sel_colors": set(colors),
        "sel_sizes": set(sizes),
        "sel_max_price": str(max_price or ""),
        "sel_min_offer": str(min_offer or ""),
        "sel_sort": sort or "",
        "sel_search": search,
        "sel_offer": offer,
    })

def products_page(request):
    # Just render page, filtering is done via JS + API
    return render(request, "products/products_page.html")

@api_view(["GET"])
@permission_classes([AllowAny])
def check_product_pincode(request):
    product_id = request.GET.get("product_id")
    pincode = (request.GET.get("pincode") or "").strip()

    # validate product_id
    if not product_id or not str(product_id).isdigit():
        return Response({"success": False, "error": "product_id is required"}, status=400)

    # validate pincode
    if len(pincode) != 6 or not pincode.isdigit():
        return Response({"success": False, "error": "Enter valid 6 digit pincode"}, status=400)

    product = Product.objects.filter(id=int(product_id)).first()
    if not product:
        return Response({"success": False, "error": "Product not found"}, status=404)

    # 1) is pincode serviceable?
    pin_obj = ServiceablePincode.objects.filter(pincode=pincode).first()
    if not pin_obj:
        return Response({
            "success": True,
            "deliverable": False,
            "product_available": False,
            "pincode": pincode,
            "message": "Sorry! We do not deliver to this pincode."
        }, status=200)

    # 2) product availability in this pincode
    avail = ProductPincodeAvailability.objects.filter(
        product=product,
        pincode=pin_obj
    ).first()

    # if entry not created in admin
    if not avail:
        return Response({
            "success": True,
            "deliverable": True,
            "product_available": False,
            "pincode": pincode,
            "city": pin_obj.city,
            "state": pin_obj.state,
            "message": "Delivery available, but this product is not available at your location"
        }, status=200)

    # if explicitly not available or stock 0
    if (not avail.is_available) or (avail.stock is not None and avail.stock <= 0):
        return Response({
            "success": True,
            "deliverable": True,
            "product_available": False,
            "pincode": pincode,
            "city": pin_obj.city,
            "state": pin_obj.state,
            "message": "Out of stock at your location"
        }, status=200)

    return Response({
        "success": True,
        "deliverable": True,
        "product_available": True,
        "pincode": pincode,
        "city": pin_obj.city,
        "state": pin_obj.state,
        "stock": int(avail.stock or 0),
        "cod_available": bool(avail.cod_available),
        "eta_days": int(avail.eta_days or 0)
    }, status=200)


@api_view(["GET"])
def stock_map_api(request):
    """
    GET /api/products/stock-map/?ids=1,2,3
    returns: { "1": true, "2": false }
    """
    ids = request.GET.get("ids", "")
    id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()]

    stock = {}
    for pid in id_list:
        # in_stock if ANY size has stock > 0
        has_stock = ProductSize.objects.filter(product_id=pid, stock__gt=0).exists()
        stock[str(pid)] = has_stock

    return Response(stock)


