from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/v1/auth/', include('api.v1.auth.urls', namespace='auth')),
    path('api/v1/projects/', include('api.v1.projects.urls', namespace='projects')),
    path('api/v1/feedbacks/', include('api.v1.feedbacks.urls', namespace='feedbacks')),
    path('api/v1/proposals/', include('api.v1.proposals.urls', namespace='proposals')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
