from django.conf.urls.defaults import *
from django.conf import settings
from core import views

urlpatterns = patterns(
    '',
    url(r'^$', views.NetworkX.as_view(), {}, name='homepage'),
    url(r'^data.json$', views.NetworkXData.as_view(), {}, name='data'),
    url(r'^view/(?P<graph_id>\d+)/$', views.NetworkX.as_view(), {}, name='view'),
    url(r'^help/$', views.Help.as_view(), {}, name='help'),
)

if settings.DEBUG:
  urlpatterns += patterns(
      '',
      url(r'^500/$', 'django.views.generic.simple.direct_to_template', {'template': '500.html'}),
      url(r'^404/$', 'django.views.generic.simple.direct_to_template', {'template': '404.html'}),
  )
