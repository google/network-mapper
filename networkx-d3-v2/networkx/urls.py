from django.conf.urls import *


urlpatterns = patterns(
    '',
    (r'^graph/', include('graph.urls')),
    (r'', include('auth.urls')),
    (r'^appengine_sessions/', include('appengine_sessions.urls')),
    (r'', include('core.urls')),
)
