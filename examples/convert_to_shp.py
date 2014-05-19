#!/usr/bin/python
import pygeo.io.convert as cc
convertor = cc.convert('clt', '/home/aashish/workspace/data/documents/clt.nc', 'clt_shp')
convertor.run()
