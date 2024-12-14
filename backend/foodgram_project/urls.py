from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from shopping_cart.views import DownloadShoppingCartView

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'docs/',
        TemplateView.as_view(template_name='redoc.html'),
        name='redoc'
    ),
    path(
        'api/recipes/download_shopping_cart/',
        DownloadShoppingCartView.as_view(),
        name='download-shopping-cart'
    ),
    path(
        'api/',
        include('recipes.urls', namespace='recipes')
    ),
    path(
        'api/',
        include('favorite.urls', namespace='favorite')
    ),
    path(
        'api/',
        include('shopping_cart.urls', namespace='shopping_cart')
    ),
    path(
        'api/',
        include('users.urls', namespace='users')
    ),
    path(
        'api/',
        include('tags.urls', namespace='tags')
    ),
    path(
        'api/',
        include('ingredients.urls', namespace='ingredients')
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
