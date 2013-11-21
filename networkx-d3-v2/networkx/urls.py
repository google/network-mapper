"""All URL pattern matchers."""

from django.conf.urls import *
from django.conf import settings

import views

urlpatterns = patterns(
    '',
    (r'', include('auth.urls')),
    (r'^appengine_sessions/', include('appengine_sessions.urls')),

    # Primary urls.
    (r'^$', views.viewUI),
    (r'^view/(?P<vis_id>\d+)$', views.viewUI),
    # The standalone suffix only shows the visualization - with no other UI.
    (r'^view/(?P<vis_id>\d+)/standalone$', views.viewVis),
    # data.json gives a list of *all* the visualizations, as opposed to data for
    # a specific visualization.
    (r'^data.json$', views.getIndexData),
    (r'^help/', views.viewHelp),

    # Vis urls.
    (r'^data/(?P<vis_id>\d+)$', views.getJSONData),
    (r'^log/(?P<vis_id>\d+)$', views.getLog),
    # url(r'^log/(?P<vis_id>\d+)$',
        # google_login_required(views.ErrorLog.as_view()), {}, name='log'),

    # RESTful interaction with visualizations.
    (r'^create/$', views.createVis),
    (r'^update/(?P<vis_id>\d+)/$', views.updateVis),
    (r'^refresh/(?P<vis_id>\d+)/$', views.refreshVis),
    (r'^delete/(?P<vis_id>\d+)/$', views.deleteVis),

    # POST sends a thumbnail. GET retrievs one, if it exists.
    (r'^thumbs/(?P<vis_id>\d+)/$', views.thumbs),
)
