from django.conf.urls.static import static
from django.conf.urls import include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.urls import path
from django.contrib import admin


admin.autodiscover()
admin.site.enable_nav_sidebar = False


urlpatterns = [
    # path('robots.txt', RobotsView.as_view(), name='robots_txt'),
    # path('', include('djangocms4test.urls')),
    # path('admin/doc/', include('django.contrib.admindocs.urls')),
]

urlpatterns = urlpatterns + i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("cms.urls")),
)

if settings.DEBUG and settings.MEDIA_ROOT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
