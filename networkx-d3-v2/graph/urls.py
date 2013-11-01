from django.conf.urls import patterns, url
from auth.decorators import google_login_required

from graph import views

urlpatterns = patterns(
    '',
    url(r'^api/spreadsheets/', views.SpreadsheetList.as_view(), name='spreadsheet_list'),
    url(r'^(?P<graph_id>\d+)/data.json$', views.GraphData.as_view(), {}, name='graph_data'),
    url(r'^(?P<graph_id>\d+)/update/$',
        google_login_required(views.GraphUpdate.as_view()), {}, name='graph_update'),
    url(r'^(?P<graph_id>\d+)/delete/$',
        google_login_required(views.GraphDeleteView.as_view()), {}, name='graph_delete'),
    url(r'^(?P<graph_id>\d+)/reload/$',
        google_login_required(views.GraphReloadView.as_view()), {}, name='graph_reload'),
    url(r'^create/$',
        google_login_required(views.GraphCreate.as_view()), {}, name='graph_create'),
    url(r'^(?P<graph_id>\d+)$', views.GraphDetailView.as_view(), {}, name='graph_detail'),
    url(r'^(?P<graph_id>\d+)/standalone/$', views.GraphStandaloneView.as_view(), {}, name='graph_standalone'),
    url(r'^(?P<graph_id>\d+)/embed/$', views.GraphView.as_view(), {}, name='graph'),
    url(r'^(?P<graph_id>\d+)/(?P<node_id>\d+)/node.json$', views.NodeDetail.as_view(), {}, name='node_detail'),
    url(r'^(?P<graph_id>\d+)/log/$',
        google_login_required(views.GraphErrorLog.as_view()), {}, name='graph_error_log'),
    )
