"""shapeEditor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib.gis import admin
import shapeEditor.shapefiles.views
import shapeEditor.tms.urls

urlpatterns = [
    url(r'^$', shapeEditor.shapefiles.views.listShapefiles),
    url(r'^import$', shapeEditor.shapefiles.views.importShapefile),
    url(r'^export/(?P<shapefile_id>\d+)$', shapeEditor.shapefiles.views.exportShapefile),
    url(r'^export/(?P<shapefile_id>\d+)/(?P<dst_epsg>\d+)/(?P<driver_code>\d+)$', shapeEditor.shapefiles.views.exportShapefile_SRC),
    url(r'^edit/(?P<shapefile_id>\d+)$', shapeEditor.shapefiles.views.editShapefile),
    url(r'^delete/(?P<shapefile_id>\d+)$', shapeEditor.shapefiles.views.deleteShapefile),
    url(r'^findFeature$', shapeEditor.shapefiles.views.findFeature),
    url(r'^addFeature/(?P<shapefile_id>\d+)$', shapeEditor.shapefiles.views.editFeature), 
    url(r'^editFeature/(?P<shapefile_id>\d+)/' + r'(?P<feature_id>\d+)$', shapeEditor.shapefiles.views.editFeature),
    url(r'^deleteFeature/(?P<shapefile_id>\d+)/' + r'(?P<feature_id>\d+)$', shapeEditor.shapefiles.views.deleteFeature),
        
    # Our TMS Server URLs:

    url(r'^admin/', include(admin.site.urls)),
    url(r'^tms/', include(shapeEditor.tms.urls)),

]
