from django.conf.urls.defaults import *
from appengine_sessions import views

urlpatterns = patterns(
    '',
    url(r'^clean-up/$', views.SessionCleanUpCron.as_view(), {}, name='session-clean-up'),
)
