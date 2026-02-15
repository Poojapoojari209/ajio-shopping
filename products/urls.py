from django.urls import path,  re_path
from .views import product_list, product_detail, category_list, brand_list, category_products
# from .page_views import product_detail_page
from . import views


urlpatterns = [
    # -------- API --------
    path('api/products/', views.product_list, name='product-list'),
    path('api/products/<int:pk>/', views.product_detail_api, name='product-detail-api'),
     path("api/check-product-pincode/", views.check_product_pincode, name="check_product_pincode"),

    path('categories/', views.category_list, name='category-list'),
    path('brands/', views.brand_list, name='brand_list'),

    path("api/products/stock-map/", views.stock_map_api, name="stock_map_api"),

    # -------- Pages --------
    # path("products-page/", views.products_page, name="products_page"),
    
    path('detail/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # for filter
    # path('<slug:gender>/<slug:category>/<slug:subcategory>/',
    #      views.category_products,
    #      name='category_products'),

    re_path(
        r'^(?P<gender>men|women|kids|beauty|homekitchen)/(?P<category>[-\w]+)/(?P<subcategory>[-\w]+)/$',
        views.category_products,
        name='category_products'
    ),

    # path('<slug:gender>/<slug:subcategory>/', views.category_products, name='category_list'),
]