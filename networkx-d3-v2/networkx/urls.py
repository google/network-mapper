"""All URL pattern matchers."""
from django.conf.urls import *

import ui_views as ui
import vis_views as vis

from auth.decorators import google_login_required


urlpatterns = patterns(
    '',
    (r'', include('auth.urls')),
    (r'^appengine_sessions/', include('appengine_sessions.urls')),

    # Primary urls.
    url(r'^$', ui.NetworkX.as_view(), {}, name='homepage'),
    url(r'^view/(?P<vis_id>\d+)$', ui.NetworkX.as_view(), {}, name='view'),
    # The standalone suffix only shows the visualization - with no other UI.
    url(r'^view/(?P<vis_id>\d+)/standalone$', vis.VisView.as_view(), {}, name='view'),
    # data.json gives a list of *all* the visualizations, as opposed to data for
    # a specific visualization.
    url(r'^data.json$', ui.NetworkXData.as_view(), {}, name='data'),
    url(r'^help/$', ui.Help.as_view(), {}, name='help'),

    # Vis urls.
    url(r'^data/(?P<vis_id>\d+)$',
        google_login_required(vis.Data.as_view()), {}, name='data'),
    url(r'^log/(?P<vis_id>\d+)$',
        google_login_required(vis.ErrorLog.as_view()), {}, name='log'),

    # POST actions. All for modifying visualizations.
    (r'^create/$', vis.createVis),
    (r'^update/(?P<vis_id>\d+)/$', vis.updateVis),
    (r'^refresh/(?P<vis_id>\d+)/$', vis.refreshVis),
    (r'^delete/(?P<vis_id>\d+)/$', vis.deleteVis),
)
