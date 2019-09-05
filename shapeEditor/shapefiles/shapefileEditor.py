# -*- coding: utf-8 -*-
# shapefileEditor.py
#
# Estes modulo implementa los logicas necearias para eprmitir al usuario ver y editar
# las features de un shapefile usando un "OpenLayers map widget".

from django import forms
from django.contrib.gis import admin

from shapeEditor.shared.models import Feature
from shapeEditor.shared import utils

#############################################################################

# Esta subclase de GeoModelAdmin nos permite conectar nuestra versi�n personalizada de
# la prantilla openlayers.html.

class OurGeoModelAdmin(admin.GeoModelAdmin):
    map_template = 'ourOpenlayers.html'

# Las siguientes clases le dicen a GeoDjango como configurar una interfaz de administrador para un
# Feature al editar varios tipos de feature.

class PointAdmin(OurGeoModelAdmin):
    fields = ['geom_singlepoint']

class LineStringAdmin(OurGeoModelAdmin):
    fields = ['geom_linestring']

class PolygonAdmin(OurGeoModelAdmin):
    fields = ['geom_polygon']

class MultiPointAdmin(OurGeoModelAdmin):
    fields = ['geom_multipoint']

class MultiLineStringAdmin(OurGeoModelAdmin):
    fields = ['geom_multilinestring']

class MultiPolygonAdmin(OurGeoModelAdmin):
    fields = ['geom_multipolygon']

class GeometryCollectionAdmin(OurGeoModelAdmin):
    fields = ['geom_geometrycollection']

#############################################################################

def getMapForm(shapefile):
    """ Devuelve un form. Subclase Form para editar las features del shapefile.
        El formulario tendrá un solo campo, 'geometría', que permite al usuario editar
        La geometría del feature.
    """

    geometryField = utils.calc_geometry_field(shapefile.geom_type)
    geometryType  = utils.calcGeometryFieldType(shapefile.geom_type)

    if geometryType == "Point":
        adminType = PointAdmin
    elif geometryType == "LineString":
        adminType = LineStringAdmin
    elif geometryType == "Polygon":
        adminType = PolygonAdmin
    elif geometryType == "MultiPoint":
        adminType = MultiPointAdmin
    elif geometryType == "MultiLineString":
        adminType = MultiLineStringAdmin
    elif geometryType == "MultiPolygon":
        adminType = MultiPolygonAdmin
    elif geometryType == "GeometryCollection":
        adminType = GeometryCollectionAdmin

    adminInstance = adminType(Feature, admin.site)
    field  = Feature._meta.get_field(geometryField)

    widgetType = adminInstance.get_map_widget(field)

    # Defina un formulario que encapsule el campo de edición deseado.

    class MapForm(forms.Form):
        geometry = forms.CharField(widget=widgetType(),
                                   label="")

    return MapForm