from django.conf.urls import *

import views

urlpatterns = patterns(
    '',
    (r'^graph/', include('graph.urls')),
    (r'', include('auth.urls')),
    (r'^appengine_sessions/', include('appengine_sessions.urls')),

    # Primary urls.
    url(r'^$', views.NetworkX.as_view(), {}, name='homepage'),
    url(r'^view/(?P<vis_id>\d+)/$', views.NetworkX.as_view(), {}, name='view'),
    # The standalone suffix only shows the visualization - with no other UI.
    url(r'^view/(?P<vis_id>\d+)/standalone$', views.Vis.as_view(), {}, name='view'),
    # data.json gives a list of *all* the visualizations, as opposed to data for
    # a specific visualization.
    url(r'^data.json$', views.NetworkXData.as_view(), {}, name='data'),
    url(r'^help/$', views.Help.as_view(), {}, name='help'),
)
