# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models
# Create your models here.

class Shapefile(models.Model):
    filename = models.CharField(max_length=255)
    srs_wkt = models.CharField(max_length=500)
    geom_type = models.CharField(max_length=50)
    def __str__(self):
        return self.filename        
    
class Attribute(models.Model):
    shapefile = models.ForeignKey(Shapefile)
    name = models.CharField(max_length=255)
    type = models.IntegerField()
    width = models.IntegerField()
    precision = models.IntegerField()
    def __str__(self):
        return self.name
    
class Feature(models.Model):
    shapefile = models.ForeignKey(Shapefile)
    geom_point = models.PointField(srid=4326,
                                    blank=True, null=True)
    geom_multipoint = \
            models.MultiPointField(srid=4326,
                                    blank=True, null=True)
    geom_multilinestring = \
            models.MultiLineStringField(srid=4326,
                                        blank=True, null=True)
    geom_multipolygon = \
            models.MultiPolygonField(srid=4326,
                                    blank=True, null=True)
    geom_geometrycollection = \
            models.GeometryCollectionField(srid=4326,
                                            blank=True,
                                            null=True)
    objects = models.GeoManager()
    def __str__(self):
        return str(self.id)
    
    def __unicode__(self):
        for geom in [self.geom_singlepoint, self.geom_multipoint,
                     self.geom_multilinestring, self.geom_multipolygon,
                     self.geom_geometrycollection]:
            if geom != None:
                return str(geom)
        return "id " + str(self.id)

class AttributeValue(models.Model):
    feature = models.ForeignKey(Feature)
    attribute = models.ForeignKey(Attribute)
    value = models.CharField(max_length=255, blank=True, null=True)
    def __unicode__(self):
        return self.value
        