from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Health check endpoint
def health_check(request):
    return JsonResponse({"status": "healthy", "service": "bibliflow"})

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check),
    
    # API Documentation with drf-spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    

]


try:
    from apps.books import urls as books_urls
    urlpatterns.append(path('api/books/', include(books_urls)))
except ImportError:
    pass

try:
    from apps.imports import urls as imports_urls
    urlpatterns.append(path('api/imports/', include(imports_urls)))
except ImportError:
    pass


try:
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
except ImportError:
    pass
