from django.conf.urls import patterns, url

from perfdash import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^data$', views.data_as_tsv, name='data_as_tsv')
)
