from django.urls import include, path
from rest_framework import routers

from .views import TagsViewSet

app_name = 'tags'

router_v1 = routers.DefaultRouter()
router_v1.register(r'tags', TagsViewSet, basename='tags')

urlpatterns = [
    path('', include(router_v1.urls)),
]
