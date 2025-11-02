from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    # Import job management
    path('', views.ImportJobCreateView.as_view(), name='import-create'),
    path('jobs/', views.ImportJobListView.as_view(), name='import-list'),
    path('jobs/<int:pk>/status/', views.ImportJobStatusView.as_view(), name='import-status'),
    path('jobs/<int:pk>/errors/', views.ImportJobErrorsView.as_view(), name='import-errors'),
    path('jobs/<int:pk>/retry/', views.ImportJobRetryView.as_view(), name='import-retry'),
    path('jobs/<int:pk>/cancel/', views.ImportJobCancelView.as_view(), name='import-cancel'),
]