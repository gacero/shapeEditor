# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render_to_response
from shapeEditor.shapefiles import shapefileIO
from django.http import HttpResponse, HttpResponseRedirect, Http404
from shapeEditor.shared.models import Shapefile, Feature
from shapeEditor.shapefiles.forms import ImportShapefileForm
import traceback
from django.contrib.gis.geos import Point
from shapeEditor.shared import utils
from osgeo import osr, ogr

from django.template import RequestContext  #github
from shapeEditor.shapefiles import shapefileEditor #github

#############################################################################

def listShapefiles(request):
    """ Muestra una lista de shapefiles disponibles.
    """
    shapefiles = Shapefile.objects.all().order_by('filename')
    return render_to_response("listShapefiles.html",
                              {'shapefiles' : shapefiles})

#############################################################################

def importShapefile(request):
    """ Permite importar un nuevo shapefile
    """
    if request.method == "GET":
        form = ImportShapefileForm()
        return render_to_response("importShapefile.html",
                                  {'form'   : form,
                                   'errMsg' : None})
    elif request.method == "POST":
        errMsg = None

        form = ImportShapefileForm(request.POST, request.FILES)
        if form.is_valid():
            shapefile = request.FILES['import_file']
           
            errMsg = shapefileIO.import_data(shapefile)
            if errMsg == None:
                return HttpResponseRedirect("/")

        return render_to_response("importShapefile.html",
                                  {'form'   : form,
                                   'errMsg' : errMsg})

#############################################################################

def exportShapefile(request, shapefile_id):
    """ El usuario exporta el shapefile elegido
    """
    try:
        shapefile = Shapefile.objects.get(id=shapefile_id)
    except Shapefile.DoesNotExist:
        raise Http404("No existe el shapefile")

    return render_to_response("select_src_export.html",
                              {'shapefile':shapefile})   

def exportShapefile_SRC(request, shapefile_id, dst_epsg, driver_code):
    '''
    El usuario exporta el shapefile elegido en el sistema de coordenadas deseado
    '''
    
    #Diccionario que relacciona los codigos de formato con el nombre del formato de salida:
    code_name = {'1': 'ESRI Shapefile', '2': 'GeoJson'}
    
    #Diccionario que relaciona los codigos de formato con su extension
    code_extension = {'1': '.shp', '2': '.json'}
    
    try:
        shapefile = Shapefile.objects.get(id=shapefile_id)
    except Shapefile.DoesNotExist:
        raise Http404("No existe el shapefile")
    
    try:
        dst_spatial_ref = osr.SpatialReference()
        dst_spatial_ref.ImportFromEPSG(int(dst_epsg))
    except:
        raise Http404("No existe el sistema de referencia.")
    
    try:
        driver_name = code_name.get(driver_code)
        driver = ogr.GetDriverByName(str(driver_name))
    except:
        raise Http404("No existe el formato de salida indicado")
    
    try:
        extension =code_extension.get(driver_code)
    except:
        raise Http404("Error al calcular la extension del archivo")
    
    return shapefileIO.export_data(shapefile, dst_spatial_ref, driver, extension)


#############################################################################

def editShapefile(request, shapefile_id):
    """ Permite al usuario editar el shapefile.
        Se muestra un mapa de  OpenLayers con el contenido de dicho shape.
        Si el ussuario hace click en una feature, es redireccionado
        a un widget de edicion de la feature seleccionada.
    """
    shapefile      = Shapefile.objects.get(id=shapefile_id)
    tmsURL         = "http://" + request.get_host()+"/tms/"
    findFeatureURL = "http://" + request.get_host()+"/findFeature"
    addFeatureURL  = "http://" + request.get_host()+ "/addFeature/" + str(shapefile_id)

    return render_to_response("selectFeature.html",
                              {'shapefile'      : shapefile,
                               'tmsURL'         : tmsURL,
                               'findFeatureURL' : findFeatureURL,
                               'addFeatureURL'  : addFeatureURL})

#############################################################################

def deleteShapefile(request, shapefile_id):
    """ Pemrite al ussuario borrar un shapefile
    """
    shapefile = Shapefile.objects.get(id=shapefile_id)

    if request.method == "POST":
        if request.POST['confirm'] == "1":
            shapefile.delete()
        return HttpResponseRedirect("/")

    return render_to_response("deleteShapefile.html",
                              {'shapefile' : shapefile})

#############################################################################

def findFeature(request):
    """ Comprueba que el usuario haya hecho click en una feature del shapefile.
    """
    try:
        shapefile_id = int(request.GET['shapefile_id'])
        latitude     = float(request.GET['latitude'])
        longitude    = float(request.GET['longitude'])

        shapefile = Shapefile.objects.get(id=shapefile_id)
        pt = Point(longitude, latitude)
        radius = utils.calc_search_radius(latitude, longitude, 100) # 100 meters.

        if shapefile.geom_type == "Point":
            query = Feature.objects.filter(geom_singlepoint__dwithin=(pt, radius))
        elif shapefile.geom_type in ["LineString", "MultiLineString"]:
            query = Feature.objects.filter(geom_multilinestring__dwithin=(pt, radius))
        elif shapefile.geom_type in ["Polygon", "MultiPolygon"]:
            query = Feature.objects.filter(geom_multipolygon__dwithin=(pt, radius))
        elif shapefile.geom_type == "MultiPoint":
            query = Feature.objects.filter(geom_multipoint__dwithin=(pt, radius))
        elif shapefile.geom_type == "GeometryCollection":
            query = Feature.objects.filter(geom_geometrycollection__dwithin=(pt, radius))
        else:
            print "Unsupported geometry: " + Feature.geom_type
            return ""

        if query.count() != 1:
            # We don't have exactly one hit -> ignore the click.
            return HttpResponse("")

        # Success!  Redirect the user to the "edit" view for the selected
        # feature.

        feature = query.all()[0]
        return HttpResponse("/editFeature/" +\
                            str(shapefile_id) + "/" + str(feature.id))
    except:
        traceback.print_exc()
        return HttpResponse("")

#############################################################################

def editFeature(request, shapefile_id, feature_id=None):
    """ Permite al usuario añadir o editar una feature del shapefile.
        el campo 'feature_id' será None if we are adding a new feature.
    """
    shapefile = Shapefile.objects.get(id=shapefile_id)

    if request.method == "POST" and "delete" in request.POST:
        # User clicked on the "Delete" button -> show "Delete Feature" page.
        return HttpResponseRedirect("/deleteFeature/" +
                                    shapefile_id + "/" + feature_id)

    geometryField = utils.calc_geometry_field(shapefile.geom_type)

    formType = shapefileEditor.getMapForm(shapefile)

    if feature_id == None:
        # Annadiendo una nueva feature.
        feature = Feature(shapefile=shapefile)
        attributes = []
    else:
        # Editando una feature.
        feature = Feature.objects.get(id=feature_id)

    # Toma los atributos para esta feature.

    attributes = []
    for attrValue in feature.attributevalue_set.all():
        attributes.append([attrValue.attribute.name,
                           attrValue.value])
    attributes.sort()

    # Muestra el formulario

    if request.method == "GET":
        wkt = getattr(feature, geometryField)
        form = formType({'geometry' : wkt})
        return render_to_response("editFeature.html",
                                  {'shapefile'  : shapefile,
                                   'form'       : form,
                                   'attributes' : attributes})
    elif request.method == "POST":
        form = formType(request.POST)
        try:
            if form.is_valid():
                wkt = form.cleaned_data['geometry']
                setattr(feature, geometryField, wkt)
                feature.save()
                # Devuelve al usuario a la pagina de seleccion de features.
                return HttpResponseRedirect("/edit/" +
                                            shapefile_id)
        except ValueError:
            pass

        return render_to_response("editFeature.html",
                                  {'shapefile'  : shapefile,
                                   'form'       : form,
                                   'attributes' : attributes})

#############################################################################

def deleteFeature(request, shapefile_id, feature_id):
    """ Permite borrar una feature.
    """
    feature = Feature.objects.get(id=feature_id)

    if request.method == "GET":
        return render_to_response("deleteFeature.html",
                                  {'feature' : feature})
    elif request.method == "POST":
        if request.POST['confirm'] == "1":
            feature.delete()
        # Return the user to the "select feature" page.
        return HttpResponseRedirect("/edit/" +
                                    shapefile_id)
        
#############################################################################

