# -*- coding: utf-8 -*-
from shapeEditor.shared.models import AttributeValue, Shapefile, Attribute, Feature
import os, os.path, tempfile, zipfile, shutil, traceback
from osgeo import ogr, osr
from django.contrib.gis.geos.geometry import GEOSGeometry
from shapeEditor.shared import utils
from django.http import FileResponse

def import_data(shapefile):
    # Copia el archivo zip en un archivo temporal

    fd,fname = tempfile.mkstemp(suffix=".zip")
    os.close(fd)

    f = open(fname, "wb")
    for chunk in shapefile.chunks():
        f.write(chunk)
    f.close()

    # Se abre el zip y se chequea su contenido.

    if not zipfile.is_zipfile(fname):
        os.remove(fname)
        return "No es un archivo zip válido."

    zip = zipfile.ZipFile(fname)
    
    #Diferenciacion de los archivos requeridos segun el formato del archivo de entrada

    es_shp = False
    for info in zip.infolist():
        extension = os.path.splitext(info.filename)[1].lower()
        if extension == '.shp':
            es_shp = True
    
    #Sie s un shp, se aplica una comprobación de que todos los archivos necearios estén en el zip
    if es_shp: 
        required_suffixes = [".shp", ".shx", ".dbf", ".prj"]
        hasSuffix = {}
        for suffix in required_suffixes:
            hasSuffix[suffix] = False
    
        for info in zip.infolist():
            extension = os.path.splitext(info.filename)[1].lower()
            if extension in required_suffixes:
                hasSuffix[extension] = True
            else:
                print "Archivo extraño: " + info.filename
    
        for suffix in required_suffixes:
            if not hasSuffix[suffix]:
                zip.close()
                os.remove(fname)
                return "No se encuentra el archivo " + suffix + " requerido"
            
    else:
        zip.close()
    
    # Descomprime el zip en un directorio temporal.
    # Se toma el nombre del archivo principal.
        
    zip = zipfile.ZipFile(fname)
    shapefileName = None
    dirname = tempfile.mkdtemp()
    for info in zip.infolist():
        if info.filename.endswith(".shp") and es_shp:
            shapefileName = info.filename
        if not es_shp:
            shapefileName = info.filename
            
        dst_file = os.path.join(dirname, info.filename)
        f = open(dst_file, "wb")
        f.write(zip.read(info.filename))
        f.close()
    zip.close()

    # Intenta abrir el archivo

    try:
        datasource  = ogr.Open(os.path.join(dirname, shapefileName))
        layer       = datasource.GetLayer(0)
        shapefileOK = True
    except:
        traceback.print_exc()
        shapefileOK = False

    if not shapefileOK:
        os.remove(fname)
        shutil.rmtree(dirname)
        return "No es un archivo válido."

    # Importar los datos del shapefile abierto.
    
    feature1 = layer.GetFeature(0)
    tipo_geometria = feature1.geometry().GetGeometryType()
    feature1.Destroy()
    #geometryType  = layer.GetLayerDefn().GetGeomType()
    geometryName = ogr.GeometryTypeToName(tipo_geometria)
    geometryName = geometryName.replace(" ", "")
    src_spatial_ref = layer.GetSpatialRef()
    dst_spatial_ref = osr.SpatialReference()
    dst_spatial_ref.ImportFromEPSG(4326)         #Aqui se define que sistema de coordenadas se le asigna en la BD

    shapefile = Shapefile(filename=shapefileName,
                          srs_wkt=src_spatial_ref.ExportToWkt(),
                          geom_type=geometryName)
    shapefile.save()

    attributes = []
    layerDef = layer.GetLayerDefn()
    for i in range(layerDef.GetFieldCount()):
        fieldDef = layerDef.GetFieldDefn(i)
        attr = Attribute(shapefile=shapefile,
                         name=fieldDef.GetName(),
                         type=fieldDef.GetType(),
                         width=fieldDef.GetWidth(),
                         precision=fieldDef.GetPrecision())
        attr.save()
        attributes.append(attr)
    #layerDef.Destroy()    
    
    coordTransform = osr.CoordinateTransformation(src_spatial_ref,
                                                  dst_spatial_ref)
        
    for i in range(layer.GetFeatureCount()):
        srcFeature = layer.GetFeature(i)
        srcGeometry = srcFeature.GetGeometryRef()
        srcGeometry.Transform(coordTransform)
        geometry = GEOSGeometry(srcGeometry.ExportToWkt())
        geometry = utils.wrap_geos_geometry(geometry)
        geometryField = utils.calc_geometry_field(geometryName)
        args = {}
        args['shapefile'] = shapefile
        args[geometryField] = geometry
        feature = Feature(**args)
        feature.save()
        
        for attr in attributes:
            success,result = utils.get_ogr_feature_attribute(attr, srcFeature)
            #if not success:
                #os.remove(fname)
                #print dirname
                #shutil.rmtree(dirname)
                #shapefile.delete()
                #return result
            if success:
                attrValue = AttributeValue(feature=feature, attribute=attr, value=result)
                attrValue.save()
        
    # Finalmente, limpiarlo todo.
    datasource.Destroy()
    os.remove(fname)
    print dirname
    shutil.rmtree(dirname)

    return None # Exito.

        
####################################################################################################

def export_data(shapefile, dst_spatial_ref, driver, extension):

    shapefile.filename = os.path.splitext(shapefile.filename)[0] + str(extension)
    
    # Crea el shapefile.

    dst_dir = tempfile.mkdtemp()
    dst_file = str(os.path.join(dst_dir, shapefile.filename))

    #dst_spatial_ref = osr.SpatialReference()           #Comentado porque recibe el src de la template
    #dst_spatial_ref.ImportFromEPSG(dst_epsg)
    #dst_spatial_ref.ImportFromWkt(shapefile.srs_wkt)
    
    #driver = ogr.GetDriverByName("ESRI Shapefile")     #Comentado porque recibe el driver de la template
    datasource = driver.CreateDataSource(dst_file)

    layer = datasource.CreateLayer(str(shapefile.filename), dst_spatial_ref)

    # Define los atributos del shapefile.

    for attr in shapefile.attribute_set.all():
        field = ogr.FieldDefn(str(attr.name), attr.type)
        field.SetWidth(attr.width)
        field.SetPrecision(attr.precision)
        layer.CreateField(field)

    # Crea el sistema de coodenadas.

    src_spatial_ref = osr.SpatialReference()
    src_spatial_ref.ImportFromEPSG(4326)

    coord_transform = osr.CoordinateTransformation(
                          src_spatial_ref, dst_spatial_ref)

    # Calcula que campo de geometria contiene la geometria del shapefile's.

    geom_field = utils.calc_geometry_field(shapefile.geom_type)

    # Exporta las features.

    for feature in shapefile.feature_set.all():
        geometry = getattr(feature, geom_field)
        geometry = utils.unwrap_geos_geometry(geometry)

        dst_geometry = ogr.CreateGeometryFromWkt(geometry.wkt)
        dst_geometry.Transform(coord_transform)

        dst_feature = ogr.Feature(layer.GetLayerDefn())
        dst_feature.SetGeometry(dst_geometry)

        for attr_value in feature.attributevalue_set.all():
            utils.set_ogr_feature_attribute(
                    attr_value.attribute,
                    attr_value.value,
                    dst_feature)

        layer.CreateFeature(dst_feature)

    layer      = None
    datasource = None

    # Compreime el shapefile como archivo ZIP.

    temp = tempfile.TemporaryFile()
    zip = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)

    shapefile_name = os.path.splitext(shapefile.filename)[0]

    for fName in os.listdir(dst_dir):
        zip.write(os.path.join(dst_dir, fName), fName)

    zip.close()
    shutil.rmtree(dst_dir)

    # Devuelve el archivo ZIP.

    temp.flush()
    temp.seek(0)

    response = FileResponse(temp)
    response['Content-type'] = "application/zip"
    response['Content-Disposition'] = \
        "attachment; filename=" + shapefile_name + ".zip"
    return response

####################################################################################################
