from django.urls import path, include

urlpatterns = [
    path('api/', include('apps.books.urls')),
    path('api/', include('apps.imports.urls')),
]