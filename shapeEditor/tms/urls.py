# URLConf for the shapeEditor.tms application.
from django.conf.urls import url
from shapeEditor.tms.views import *

urlpatterns = [
	url(r'^$', root), # "/tms" llama a root()
	url(r'^(?P<version>[0-9.]+)$', service), # eg, "/tms/1.0" llama a service(version="1.0")
	url(r'^(?P<version>[0-9.]+)/(?P<shapefile_id>\d+)$', tileMap), # eg, "/tms/1.0/2" llama  a tileMap(version="1.0", shapefile_id=2)
	url(r'^(?P<version>[0-9.]+)/' +	r'(?P<shapefile_id>\d+)/(?P<zoom>\d+)/' + 
	r'(?P<x>\d+)/(?P<y>\d+)\.png$', tile), # eg, "/tms/1.0/2/3/4/5" llama a tile(version="1.0", shapefile_id=2, zoom=3, x=4, y=5)
]