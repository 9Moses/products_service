"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# Optional drf-spectacular schema views (if package installed)
try:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
    )
    SPECTACULAR_AVAILABLE = True
except Exception:
    SPECTACULAR_AVAILABLE = False

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('products.urls')),
]

if SPECTACULAR_AVAILABLE:
    urlpatterns += [
        # OpenAPI schema (JSON)
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        # Swagger UI
        path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        # Redoc UI
        path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]
