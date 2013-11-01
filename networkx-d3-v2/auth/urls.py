from django.conf.urls import patterns, url
from auth import views

urlpatterns = patterns(
    '',
    url(r'^login/?$', views.login, name='login'),
    url(r'^oauth2redirect/?$', views.oauth2redirect, name='oauth2redirect'),
    url(r'^oauth2callback/?$', views.oauth2callback, name='oauth2callback'),
    url(r'^oauth2logout/?$', views.oauth2logout, name='oauth2logout'),
    url(r'^auth-failed/?$', views.auth_failed, name='auth-failed')
)
