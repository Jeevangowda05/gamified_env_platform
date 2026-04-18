"""
Main URL configuration for Gamified Environmental Education Platform
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('teacher/', include('apps.teachers.urls', namespace='teacher')),
    path('gamification/', include('apps.gamification.urls')),
   # path('education/', include('apps.education.urls')),
    path('assessments/', include('apps.assessments.urls')),
    path('api/v1/', include([
        path('accounts/', include('apps.accounts.urls', namespace='api_accounts')),
        path('gamification/', include('apps.gamification.urls', namespace='api_gamification')),
      #  path('education/', include('apps.education.urls', namespace='api_education')),
        path('assessments/', include('apps.assessments.urls', namespace='api_assessments')),
        path('challenges/', include('apps.challenges.urls')),
    ])),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Customize admin
admin.site.site_header = "Environmental Education Platform Admin"
admin.site.site_title = "EEP Admin Portal"
admin.site.index_title = "Welcome to Environmental Education Platform Administration"
