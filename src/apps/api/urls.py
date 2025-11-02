from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.books.views import BookViewSet
from apps.imports.views import ImportJobViewSet, ImportErrorViewSet

router = DefaultRouter()
router.register("books", BookViewSet, basename="books")
router.register("imports/jobs", ImportJobViewSet, basename="imports-jobs")
router.register("imports/errors", ImportErrorViewSet, basename="imports-errors")

urlpatterns = [
    path("", include(router.urls)),

    # custom actions
    path("imports/jobs/<int:pk>/retry/", ImportJobViewSet.as_view({"post": "retry"})),
    path("imports/jobs/<int:pk>/cancel/", ImportJobViewSet.as_view({"post": "cancel"})),
]
