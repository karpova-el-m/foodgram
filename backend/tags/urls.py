from django.urls import include, path
from rest_framework import routers

from .views import TagsViewSet

app_name = 'tags'

router = routers.DefaultRouter()
router.register(r'tags', TagsViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
]
