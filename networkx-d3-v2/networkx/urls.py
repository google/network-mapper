"""All URL pattern matchers."""
from django.conf.urls import *

import ui_views as ui
import vis_views as vis

from auth.decorators import google_login_required
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = patterns(
    '',
    (r'', include('auth.urls')),
    (r'^appengine_sessions/', include('appengine_sessions.urls')),

    # Primary urls.
    (r'^$', ui.viewUI),
    (r'^view/(?P<vis_id>\d+)$', ui.viewVis),
    # The standalone suffix only shows the visualization - with no other UI.
    url(r'^view/(?P<vis_id>\d+)/standalone$', vis.VisView.as_view(), {}, name='view'),
    # data.json gives a list of *all* the visualizations, as opposed to data for
    # a specific visualization.
    (r'^data.json$', ui.getIndexData),
    (r'^help/', ui.viewHelp),

    # Vis urls.
    url(r'^data/(?P<vis_id>\d+)$',
        google_login_required(vis.Data.as_view()), {}, name='data'),
    url(r'^log/(?P<vis_id>\d+)$',
        google_login_required(vis.ErrorLog.as_view()), {}, name='log'),

    # RESTful interaction with visualizations.
    (r'^create/$', vis.createVis),
    (r'^update/(?P<vis_id>\d+)/$', vis.updateVis),
    (r'^refresh/(?P<vis_id>\d+)/$', vis.refreshVis),
    (r'^delete/(?P<vis_id>\d+)/$', vis.deleteVis),
)
