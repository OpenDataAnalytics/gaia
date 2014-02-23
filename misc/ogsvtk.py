#!/usr/bin/python
'''
Demonstrates creating content on server, serializing it, and rendering over a map in the client.
See default response for examples of usage.
'''
import cherrypy
import sys
import os

vtkOK = False
try:
  import vtk
  vtkOK = True
except ImportError:
  print("VTK NOT AVAILABLE")

class VTKRoot(object):
    def __init__(self, host, port, ssl=False):
        self.host = host
        self.port = port
        self.scheme = 'wss' if ssl else 'ws'
        self.pointString = "aQMAAFAyAAAAAAAAAAAAAAAAAAA/AAAAAAAAAAAAAAC/AiZePgAAAADlpeY+HCbIPgAAAAAHnZ8+4JT5PgAAAACH3OM94JT5PgAAAACH3OO9HCbIPgAAAAAHnZ++AiZePgAAAADlpea+KxUdPisVHT7lpeY+0IaNPtCGjT4HnZ8+FnuwPhZ7sD6H3OM9FnuwPhZ7sD6H3OO90IaNPtCGjT4HnZ++KxUdPisVHT7lpea+Pwt1IwImXj7lpeY+58bcIxwmyD4HnZ8+9aYJJOCU+T6H3OM99aYJJOCU+T6H3OO958bcIxwmyD4HnZ++Pwt1IwImXj7lpea+KxUdvisVHT7lpeY+0IaNvtCGjT4HnZ8+FnuwvhZ7sD6H3OM9FnuwvhZ7sD6H3OO90IaNvtCGjT4HnZ++KxUdvisVHT7lpea+AiZevj8L9SPlpeY+HCbIvufGXCQHnZ8+4JT5vvWmiSSH3OM94JT5vvWmiSSH3OO9HCbIvufGXCQHnZ++AiZevj8L9SPlpea+KxUdvisVHb7lpeY+0IaNvtCGjb4HnZ8+FnuwvhZ7sL6H3OM9FnuwvhZ7sL6H3OO90IaNvtCGjb4HnZ++KxUdvisVHb7lpea+b8g3pAImXr7lpeY+LZWlpBwmyL4HnZ8+cHrOpOCU+b6H3OM9cHrOpOCU+b6H3OO9LZWlpBwmyL4HnZ++b8g3pAImXr7lpea+KxUdPisVHb7lpeY+0IaNPtCGjb4HnZ8+FnuwPhZ7sL6H3OM9FnuwPhZ7sL6H3OO90IaNPtCGjb4HnZ++KxUdPisVHb7lpea+7oZp/32g+f/aWUf/1E5B/+VvVv/3qIn/59fO/7PN+//KOzf/tAQm/8MuMf/odlz/9cGp/8TW8//aWUf/1E5B/+VvVv/3qIn/59fO/7PN+//zlHX/97OW/+zTxf/L2O7/pcP+/4ir/f/2wKf/0tvo/5q7//9rjfD/VnTg/1185v/wzrz/tc76/3GT9P9GXs//O0zA/0xm1v/2wKf/0tvo/5q7//9rjfD/VnTg/1185v/zlHX/97OW/+zTxf/L2O7/pcP+/4ir/f8AAIA/AAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAAAAAAAAAAAAAACAPwAAAAAAAAAAAAAAAAAAAAAAAIA/"
        self.lineString = "zQwAAEx9AAAAAAAAwAAAAMAAAADAAACAvwAAAMAAAADAAACAvwAAgL8AAADAAAAAwAAAgL8AAADAAAAAwAAAAMAAAIC/AACAvwAAAMAAAIC/AACAvwAAgL8AAIC/AAAAwAAAgL8AAIC/AAAAAAAAAMAAAADAAAAAAAAAgL8AAADAAAAAAAAAAMAAAIC/AAAAAAAAgL8AAIC/AACAPwAAAMAAAADAAACAPwAAgL8AAADAAACAPwAAAMAAAIC/AACAPwAAgL8AAIC/AAAAQAAAAMAAAADAAAAAQAAAgL8AAADAAAAAQAAAAMAAAIC/AAAAQAAAgL8AAIC/AACAvwAAAAAAAADAAAAAwAAAAAAAAADAAACAvwAAAAAAAIC/AAAAwAAAAAAAAIC/AAAAAAAAAAAAAADAAAAAAAAAAAAAAIC/AACAPwAAAAAAAADAAACAPwAAAAAAAIC/AAAAQAAAAAAAAADAAAAAQAAAAAAAAIC/AACAvwAAgD8AAADAAAAAwAAAgD8AAADAAACAvwAAgD8AAIC/AAAAwAAAgD8AAIC/AAAAAAAAgD8AAADAAAAAAAAAgD8AAIC/AACAPwAAgD8AAADAAACAPwAAgD8AAIC/AAAAQAAAgD8AAADAAAAAQAAAgD8AAIC/AACAvwAAAEAAAADAAAAAwAAAAEAAAADAAACAvwAAAEAAAIC/AAAAwAAAAEAAAIC/AAAAAAAAAEAAAADAAAAAAAAAAEAAAIC/AACAPwAAAEAAAADAAACAPwAAAEAAAIC/AAAAQAAAAEAAAADAAAAAQAAAAEAAAIC/AAAAwAAAAMAAAAAAAACAvwAAAMAAAAAAAACAvwAAgL8AAAAAAAAAwAAAgL8AAAAAAAAAAAAAAMAAAAAAAAAAAAAAgL8AAAAAAACAPwAAAMAAAAAAAACAPwAAgL8AAAAAAAAAQAAAAMAAAAAAAAAAQAAAgL8AAAAAAACAvwAAAAAAAAAAAAAAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAPwAAAAAAAAAAAAAAQAAAAAAAAAAAAACAvwAAgD8AAAAAAAAAwAAAgD8AAAAAAAAAAAAAgD8AAAAAAACAPwAAgD8AAAAAAAAAQAAAgD8AAAAAAACAvwAAAEAAAAAAAAAAwAAAAEAAAAAAAAAAAAAAAEAAAAAAAACAPwAAAEAAAAAAAAAAQAAAAEAAAAAAAAAAwAAAAMAAAIA/AACAvwAAAMAAAIA/AACAvwAAgL8AAIA/AAAAwAAAgL8AAIA/AAAAAAAAAMAAAIA/AAAAAAAAgL8AAIA/AACAPwAAAMAAAIA/AACAPwAAgL8AAIA/AAAAQAAAAMAAAIA/AAAAQAAAgL8AAIA/AACAvwAAAAAAAIA/AAAAwAAAAAAAAIA/AAAAAAAAAAAAAIA/AACAPwAAAAAAAIA/AAAAQAAAAAAAAIA/AACAvwAAgD8AAIA/AAAAwAAAgD8AAIA/AAAAAAAAgD8AAIA/AACAPwAAgD8AAIA/AAAAQAAAgD8AAIA/AACAvwAAAEAAAIA/AAAAwAAAAEAAAIA/AAAAAAAAAEAAAIA/AACAPwAAAEAAAIA/AAAAQAAAAEAAAIA/AAAAwAAAAMAAAABAAACAvwAAAMAAAABAAACAvwAAgL8AAABAAAAAwAAAgL8AAABAAAAAAAAAAMAAAABAAAAAAAAAgL8AAABAAACAPwAAAMAAAABAAACAPwAAgL8AAABAAAAAQAAAAMAAAABAAAAAQAAAgL8AAABAAACAvwAAAAAAAABAAAAAwAAAAAAAAABAAAAAAAAAAAAAAABAAACAPwAAAAAAAABAAAAAQAAAAAAAAABAAACAvwAAgD8AAABAAAAAwAAAgD8AAABAAAAAAAAAgD8AAABAAACAPwAAgD8AAABAAAAAQAAAgD8AAABAAACAvwAAAEAAAABAAAAAwAAAAEAAAABAAAAAAAAAAEAAAABAAACAPwAAAEAAAABAAAAAQAAAAEAAAABAWXfj/5a3///R2un/haj8/3WY9v/B1PT/97yh/7LM+/+dvf//293e/87a6//2o4X/gqb7/8DU9f+wyvz/8sq1/3WY9v+iwf//krT+/8zZ7f/Q2ur/e5/5//ezlv+xy/z/3N3d//KSdP+/0/b/9cSs/5q7///M2e3/osH//1Vy3//h29j/gaT7/7HL/P/vzr3/kLL+/9Lb6P9xk/T/nr7//3OW9f87TMD/ocD//1Rw3v96nfj/rsn8/2GB6f+NsP7/VHDe/2+S8/+StP7/39zZ/++Ia//T2+f/69PG/91fS//R2un/9Z+A/67J/P/o1sz/6HZc/9Xb5f/MQDn/8Y1v/+rVyf/2vaL/psT+//aggf/xzLj/wdT0/8TW8/9vkvP/09vn/7LM+/+Mr/7/dZj2/8HU9P/3vKH/ssz7/87a6//2o4X/sMr8//LKtf+StP7/zNnt//ezlv+xy/z/8pJ0//XErP/M2e3/4dvY/4Gk+//vzr3/0tvo/56+//+hwP//VHDe/67J/P+NsP7/b5Lz/1l34/+Wt///0drp/4Wo/P+dvf//293e/4Km+//A1PX/dZj2/6LB///Q2ur/e5/5/9zd3f+/0/b/mrv//6LB//9Vct//scv8/5Cy/v9xk/T/c5b1/ztMwP96nfj/YYHp/1Rw3v9YAgAAAAABAAEAAgADAAIAAAADAAQABQAFAAYABwAGAAQABwAAAAQAAQAFAAMABwACAAYAAQAIAAgACQACAAkABQAKAAoACwAGAAsACAAKAAkACwAIAAwADAANAAkADQAKAA4ADgAPAAsADwAMAA4ADQAPAAwAEAAQABEADQARAA4AEgASABMADwATABAAEgARABMAAgAUABUAFAADABUABgAWABcAFgAHABcAFQAXABQAFgAJABgAFAAYAAsAGQAWABkAGAAZAA0AGgAYABoADwAbABkAGwAaABsAEQAcABoAHAATAB0AGwAdABwAHQAUAB4AHwAeABUAHwAWACAAIQAgABcAIQAfACEAHgAgABgAIgAeACIAGQAjACAAIwAiACMAGgAkACIAJAAbACUAIwAlACQAJQAcACYAJAAmAB0AJwAlACcAJgAnAB4AKAApACgAHwApACAAKgArACoAIQArACkAKwAoACoAIgAsACgALAAjAC0AKgAtACwALQAkAC4ALAAuACUALwAtAC8ALgAvACYAMAAuADAAJwAxAC8AMQAwADEAMgAzADMANAA1ADQAMgA1AAQAMgAFADMABwA1AAYANAAzADYANgA3ADQANwAKADYACwA3ADYAOAA4ADkANwA5AA4AOAAPADkAOAA6ADoAOwA5ADsAEgA6ABMAOwA0ADwAPQA8ADUAPQAXAD0AFgA8ADcAPgA8AD4AGQA+ADkAPwA+AD8AGwA/ADsAQAA/AEAAHQBAADwAQQBCAEEAPQBCACEAQgAgAEEAPgBDAEEAQwAjAEMAPwBEAEMARAAlAEQAQABFAEQARQAnAEUAQQBGAEcARgBCAEcAKwBHACoARgBDAEgARgBIAC0ASABEAEkASABJAC8ASQBFAEoASQBKADEASgBLAEwATABNAE4ATQBLAE4AMgBLADMATAA1AE4ANABNAEwATwBPAFAATQBQADYATwA3AFAATwBRAFEAUgBQAFIAOABRADkAUgBRAFMAUwBUAFIAVAA6AFMAOwBUAE0AVQBWAFUATgBWAD0AVgA8AFUAUABXAFUAVwA+AFcAUgBYAFcAWAA/AFgAVABZAFgAWQBAAFkAVQBaAFsAWgBWAFsAQgBbAEEAWgBXAFwAWgBcAEMAXABYAF0AXABdAEQAXQBZAF4AXQBeAEUAXgBaAF8AYABfAFsAYABHAGAARgBfAFwAYQBfAGEASABhAF0AYgBhAGIASQBiAF4AYwBiAGMASgBjAGQAZQBlAGYAZwBmAGQAZwBLAGQATABlAE4AZwBNAGYAZQBoAGgAaQBmAGkATwBoAFAAaQBoAGoAagBrAGkAawBRAGoAUgBrAGoAbABsAG0AawBtAFMAbABUAG0AZgBuAG8AbgBnAG8AVgBvAFUAbgBpAHAAbgBwAFcAcABrAHEAcABxAFgAcQBtAHIAcQByAFkAcgBuAHMAdABzAG8AdABbAHQAWgBzAHAAdQBzAHUAXAB1AHEAdgB1AHYAXQB2AHIAdwB2AHcAXgB3AHMAeAB5AHgAdAB5AGAAeQBfAHgAdQB6AHgAegBhAHoAdgB7AHoAewBiAHsAdwB8AHsAfABjAHwAAACAPwAAAAAAAAAAAAAAAAAAAAAAAIA/AAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAAAAAAAAAAAAAACAPw=="
        self.meshString = "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/8MuMf/odlz/5W9W//eoif/s08X/y9ju/5q7//9rjfD/cZP0/0Zez/+au///a43w/+zTxf/L2O7/IAEAAAIACAAAAAgADgAAAA4AFAAAABQAGgAAABoAIAAAACAAJgAAACYALAAAACwAAgAAAAcAAQANAA0AAQATABMAAQAZABkAAQAfAB8AAQAlACUAAQArACsAAQAxADEAAQAHAAIAAwAJAAIACQAIAAMABAAKAAMACgAJAAQABQALAAQACwAKAAUABgAMAAUADAALAAYABwANAAYADQAMAAgACQAPAAgADwAOAAkANAAQAAkAEAAPADQANQARADQAEQAQADUADAASADUAEgARAAwADQATAAwAEwASAA4ADwAVAA4AFQAUAA8ANgAWAA8AFgAVADYANwAXADYAFwAWADcAEgAYADcAGAAXABIAEwAZABIAGQAYABQAFQAbABQAGwAaABUAOAAcABUAHAAbADgAOQAdADgAHQAcADkAGAAeADkAHgAdABgAGQAfABgAHwAeABoAGwAhABoAIQAgABsAOgAiABsAIgAhADoAOwAjADoAIwAiADsAHgAkADsAJAAjAB4AHwAlAB4AJQAkACAAIQAnACAAJwAmACEAPAAoACEAKAAnADwAPQApADwAKQAoAD0AJAAqAD0AKgApACQAJQArACQAKwAqACYAJwAtACYALQAsACcAPgAuACcALgAtAD4APwAvAD4ALwAuAD8AKgAwAD8AMAAvACoAKwAxACoAMQAwACwALQADACwAAwACAC0AQAAyAC0AMgADAEAAQQAzAEAAMwAyAEEAMAAGAEEABgAzADAAMQAHADAABwAGAAAAgD8AAAAAAAAAAAAAAAAAAAAAAACAPwAAAAAAAAAAAAAAAAAAAAAAAIA/AAAAAAAAAAAAAAAAAAAAAAAAgD8="
        self.geoString = {
                          '1':'{"type": "Point", "coordinates": [0.0,0.0]}',
                          '1.c':'{"properties": {"ScalarFormat": "rgb"}, "type": "Point", "coordinates": [0.0,0.0,0.0, 1,0,1]}',
                          '2':'{"type": "MultiPoint", "coordinates": [[0.0,0.0],[1.0,1.0],[2.0,0.0],[3.0,1.0]]}',
                          '2.c':'{"properties": {"ScalarFormat": "rgb"}, "type": "MultiPoint", "coordinates": [[0.0,0.0,0.0, 1,1,1],[1.0,1.0,0.0, 1,1,0],[2.0,0.0,0.0, 1,0,1],[3.0,1.0,0.0, 0,1,1]]}',
                          '3':'{"type": "LineString", "coordinates": [[0.0,0.0],[1.0,1.0],[2.0,0.0],[3.0,1.0]]}', #BUG
                          '3.c':'{"properties": {"ScalarFormat": "rgb"}, "type": "LineString", "coordinates": [[0.0,0.0,0.0, 1,1,1],[1.0,1.0,0.0, 1,1,0],[2.0,0.0,0.0, 1,0,1],[3.0,1.0,0.0, 0,1,1]]}', #BUG
                          '4':'{"type": "MultiLineString", "coordinates": [[[0.0, 0.0],[1.0, 1.0],[2.0, 0.0],[3.0, 1.0]],[[0.0, 2.0],[1.0, 3.0],[2.0, 2.0],[3.0, 3.0]]]}',
                          '4.c':'{"properties": {"ScalarFormat": "rgb"}, "type": "MultiLineString", "coordinates": [[[0.0,0.0,0.0, 0,0,0],[1.0,1.0,0.0, 0,0,1],[2.0,0.0,0.0, 0,1,0],[3.0,1.0,0.0, 0,1,1]],[[0.0,2.0,0.0, 1,0,0],[1.0,3.0,0.0, 1,0,1],[2.0,2.0,0.0, 1,1,0],[3.0,3.0,0.0, 1,1,1]]]}',
                          '5':'{"type": "Polygon", "coordinates": [[[0.0, 0.0],[1.0, 0.0],[0.5, 1.0]]]}', #test simplest polygon
                          '5.c':'{"properties": {"ScalarFormat": "rgb"}, "type": "Polygon", "coordinates": [[[0.0,0.0,0.0, 0,0,0],[1.0,0.0,0.0, 0,0,1],[0.5,1.0,0.0, 0,1,0]]]}', #test simplest polygon
                          '6':'{"type": "Polygon", "coordinates": [[[0.0, 0.0],[1.0, 0.0],[0.5, 1.0]],[[0.33, 0.33],[0.66, 0.33],[0.5, 0.66]]]}', #TODO: polygon with cavity
                          '7':'{"type": "Polygon", "coordinates": [[[0.0, 0.0],[1.0, 0.0],[1.0, 1.0],[0.0, 1.0]]]}', #test non simplex (but still convex) polygon
                          '7.c':'{"properties": {"ScalarFormat": "rgb"}, "type": "Polygon", "coordinates": [[[0.0,0.0,0.0, 0,0,0],[1.0,0.0,0.0, 0,0,1],[1.0,1.0,0.0, 0,1,0],[0.0,1.0,0.0, 0,1,1]]]}', #test non simplex (but still convex) polygon
                          '8':'{"type": "Polygon", "coordinates": [[[0.0, 0.0],[1.0, 0.0],[1.0, 1.0],[0.0, 1.0], [0.5, 0.5]]]}', #TODO: non simplex (now concave) polygon
                          '9':'{"type": "MultiPolygon", "coordinates": [[ [[0.0,0.0],[1.0,0.0],[0.5,1.0]] ],[ [[2.0,0.0],[3.0,0.0],[3.0,1.0],[2.0,1.0]] ]]}',
                          '9.c':'{"properties": {"ScalarFormat": "rgb"}, "type": "MultiPolygon", "coordinates": [[ [[0.0,0.0,0.0, 0,0,0],[1.0,0.0,0.0, 0,0,1],[0.5,1.0,0.0, 0,1,0]] ],[ [[2.0,0.0,0.0, 0,1,1],[3.0,0.0,0.0, 1,0,0],[3.0,1.0,0.0, 1,0,0],[2.0,1.0,0.0, 1,0,1]] ]]}',
                          '10':'{"type": "GeometryCollection", "geometries": [{"type":"Point","coordinates":[0.0, 0.0]},{"type":"Point","coordinates": [1.0, 1.0]}]}',
                          '11':'{"type": "Feature", "geometry": {"type": "Point","coordinates": [0.0, 0.0]}}',
                          '12':'{"type": "FeatureCollection", "features":[{"type": "Feature", "geometry": {"type": "Point","coordinates": [0.0, 0.0]}},{"type": "Feature", "geometry": {"type": "Point","coordinates": [1.0, 1.0]}}]}',
                          '13':'{"type": "Feature","geometry": {"type": "Polygon","coordinates": [[ [0.0, 0.0], [1.0, 0.0], [1.0, 1.0],  [0.0, 1.0], [0.0, 0.0] ] ]},"properties": {  "prop0": "value0", "prop1": {"this": "that"}}}'
                          };
        self.gjShader = """
        var mat = new ogs.vgl.material();
        var prog = new ogs.vgl.shaderProgram();
        var posVertAttr = new ogs.vgl.vertexAttribute("aVertexPosition");
        prog.addVertexAttribute(posVertAttr, ogs.vgl.vertexAttributeKeys.Position);

        if (data.scalarFormat == "none")
        {
        }
        if (data.scalarFormat == "rgb")
        {
          var vC = new ogs.vgl.vertexAttribute("aVertexColor");
          prog.addVertexAttribute(vC, ogs.vgl.vertexAttributeKeys.Color);
        }
        if (data.scalarFormat == "values")
        {
          var vS = new ogs.vgl.vertexAttribute("aVertexScalar");
          prog.addVertexAttribute(vS, ogs.vgl.vertexAttributeKeys.Scalar);

          var lut = new ogs.vgl.lookupTable();
          lut.setRange(data.scalarRange)
          //lut.setColorTable([255,0,0,255,
          //                   255,255,0,255,
          //                   0,255,0,255,
          //                   0,255,255,255,
          //                   0,0,255,255])
          mat.addAttribute(lut);

          var lutMin = new ogs.vgl.floatUniform("lutMin", lut.range()[0]);
          prog.addUniform(lutMin);
          var lutMax = new ogs.vgl.floatUniform("lutMax", lut.range()[1]);
          prog.addUniform(lutMax);
        }

        var modelViewUniform = new ogs.vgl.modelViewUniform("modelViewMatrix");
        prog.addUniform(modelViewUniform);

        var projectionUniform = new ogs.vgl.projectionUniform("projectionMatrix");
        prog.addUniform(projectionUniform);

        var vertexShaderSource;
        if (data.scalarFormat == "none")
        {
          vertexShaderSource = [
            'attribute vec3 aVertexPosition;',
            'uniform mat4 modelViewMatrix;',
            'uniform mat4 projectionMatrix;',
            'void main(void)',
            '{',
              'gl_Position = projectionMatrix * modelViewMatrix * vec4(aVertexPosition, 1.0);',
            '}'
          ].join('\\n');
        }
        if (data.scalarFormat == "rgb")
        {
          vertexShaderSource = [
            'attribute vec3 aVertexPosition;',
            'uniform mat4 modelViewMatrix;',
            'uniform mat4 projectionMatrix;',
            'attribute vec3 aVertexColor;',
            'varying vec3 vColor;',
            'void main(void)',
            '{',
              'gl_Position = projectionMatrix * modelViewMatrix * vec4(aVertexPosition, 1.0);',
              'vColor = aVertexColor;',
            '}'
          ].join('\\n');
        }
        if (data.scalarFormat == "values")
        {
          vertexShaderSource = [
            'attribute vec3 aVertexPosition;',
            'uniform mat4 modelViewMatrix;',
            'uniform mat4 projectionMatrix;',
            'attribute float aVertexScalar;',
            'uniform float lutMin, lutMax;',
            'varying float vScalar;',
            'void main(void)',
            '{',
              'gl_Position = projectionMatrix * modelViewMatrix * vec4(aVertexPosition, 1.0);',
              'vScalar = (aVertexScalar-lutMin)/(lutMax-lutMin);',
            '}'
          ].join('\\n');
        }
        console.log(vertexShaderSource);
        var vertexShader = new ogs.vgl.shader(gl.VERTEX_SHADER);
        vertexShader.setShaderSource(vertexShaderSource);
        prog.addShader(vertexShader);

        var fragmentShaderSource;
        if (data.scalarFormat == "none")
        {
          fragmentShaderSource = [
           'precision mediump float;',
           'void main(void) {',
             'gl_FragColor = vec4(1,1,1,1);',
           '}'
          ].join('\\n');
        }
        if (data.scalarFormat == "rgb")
        {
          fragmentShaderSource = [
           'precision mediump float;',
           'varying vec3 vColor;',
           'void main(void) {',
             'gl_FragColor = vec4(vColor, 1);',
           '}'
          ].join('\\n');
        }
        if (data.scalarFormat == "values")
        {
          fragmentShaderSource = [
           'precision mediump float;',
           'varying float vScalar;',
           'uniform sampler2D sampler2d;',
           'void main(void) {',
             'gl_FragColor = vec4(texture2D(sampler2d, vec2(vScalar, 0.0)).xyz, 1);',
           '}'
          ].join('\\n');
        }
        console.log(fragmentShaderSource);
        var fragmentShader = new ogs.vgl.shader(gl.FRAGMENT_SHADER);
        fragmentShader.setShaderSource(fragmentShaderSource);
        prog.addShader(fragmentShader);
        mat.addAttribute(prog);
        """

    def serveVTKWebGL(self, datasetString):
        '''
        Deliver a bjson encoded serialized vtkpolydata file and render it
        over the canonical cpipe scene.
        '''

        res = """
  <html>
    <head>
      <script type="text/javascript" src="/common/js/gl-matrix.js"></script>
      <script type="text/javascript" src="/lib/geoweb.min.js"></script>
      <script type="text/javascript" src="//ajax.googleapis.com/ajax/libs/jquery/1.9.0/jquery.min.js"></script>
      <script type="text/javascript">
      function readVTKWebGL() {
        var geom = new ogs.vgl.vtkUnpack().parseObject(\"%(datasetString)s\");

        var mapper = new ogs.vgl.mapper();
        mapper.setGeometryData(geom);
        var mat = new ogs.vgl.material();
        var prog = new ogs.vgl.shaderProgram();

        var posVertAttr = new ogs.vgl.vertexAttribute("aVertexPosition");
        prog.addVertexAttribute(posVertAttr, ogs.vgl.vertexAttributeKeys.Position);

        var posNormAttr = new ogs.vgl.vertexAttribute("aVertexNormal");
        prog.addVertexAttribute(posNormAttr, ogs.vgl.vertexAttributeKeys.Normal);

        var posColorAttr = new ogs.vgl.vertexAttribute("aVertexColor");
        prog.addVertexAttribute(posColorAttr, ogs.vgl.vertexAttributeKeys.Color);

        var modelViewUniform = new ogs.vgl.modelViewUniform("modelViewMatrix");
        prog.addUniform(modelViewUniform);

        var projectionUniform = new ogs.vgl.projectionUniform("projectionMatrix");
        prog.addUniform(projectionUniform);

        var vertexShaderSource = [
          'attribute vec3 aVertexPosition;',
          'attribute vec3 aVertexColor;',
          'uniform mat4 modelViewMatrix;',
          'uniform mat4 projectionMatrix;',
          'varying vec3 vColor;',
          'void main(void)',
          '{',
            'gl_Position = projectionMatrix * modelViewMatrix * vec4(aVertexPosition*1.0, 1.0);',
            'vColor = aVertexColor;',
          '}'
        ].join('\\n');
        var vertexShader = new ogs.vgl.shader(gl.VERTEX_SHADER);
        vertexShader.setShaderSource(vertexShaderSource);
        prog.addShader(vertexShader);

        var fragmentShaderSource = [
         'precision mediump float;',
         'varying vec3 vColor;',
         'void main(void) {',
           'gl_FragColor = vec4(vColor,1.0);',
         '}'
        ].join('\\n');
        var fragmentShader = new ogs.vgl.shader(gl.FRAGMENT_SHADER);
        fragmentShader.setShaderSource(fragmentShaderSource);
        prog.addShader(fragmentShader);

        mat.addAttribute(prog);

        var actor = new ogs.vgl.actor();
        actor.setMapper(mapper);
        actor.setMaterial(mat);
        return actor;
      }
      </script>
      <script type="text/javascript">
      function main() {
        var mapOptions = {
          zoom : 1,
          center : ogs.geo.latlng(0.0, 0.0),
          source : '/data/assets/land_shallow_topo_2048.png'
        };
        var myMap = ogs.geo.map(document.getElementById("glcanvas"), mapOptions);

        var planeLayer = ogs.geo.featureLayer({
          "opacity" : 1,
          "showAttribution" : 1,
          "visible" : 1
         },
         readVTKWebGL()
         );
        myMap.addLayer(planeLayer);
      }
      </script>

      <link rel="stylesheet" href="http://code.jquery.com/ui/1.10.1/themes/base/jquery-ui.css" />
      <script src="http://code.jquery.com/jquery-1.9.1.js"></script>
      <script src="http://code.jquery.com/ui/1.10.1/jquery-ui.js"></script>
    </head>
    <body onload="main()">
      <canvas id="glcanvas" width="800" height="600"></canvas>
    </body>
  </html>
""" % {'datasetString':datasetString}
        return res

    def serveGeoJSON(self, datasetString):
        '''
        Deliver geojson encoded data and render it over the canonical cpipe scene.
        '''

        res = ("""
  <html>
    <head>
      <script type="text/javascript" src="/common/js/gl-matrix.js"></script>
      <script type="text/javascript" src="/lib/geoweb.min.js"></script>
      <script type="text/javascript" src="//ajax.googleapis.com/ajax/libs/jquery/1.9.0/jquery.min.js"></script>
      <script type="text/javascript">
      function makedata() {
        var data = new ogs.vgl.geojsonReader().getPrimitives(\'%(datasetString)s\');
        var geoms = data.geoms;
        """ +
        self.gjShader +
        """
        var actors = [];
        for (var i = 0; i < geoms.length; i++)
          {
          var mapper = new ogs.vgl.mapper();
          mapper.setGeometryData(geoms[i]);
          var actor = new ogs.vgl.actor();
          actor.setMapper(mapper);
          actor.setMaterial(mat);
          actors.push(actor);
          }
        return actors;
      }
      </script>
      <script type="text/javascript">
      function main() {
        var mapOptions = {
          zoom : 1,
          center : ogs.geo.latlng(0.0, 0.0),
          source : '/data/assets/land_shallow_topo_2048.png'
        };
        var myMap = ogs.geo.map(document.getElementById("glcanvas"), mapOptions);
        actors = makedata();

        //TODO: change layer.js to take multiple actors
        for (var i = 0; i < actors.length; i++)
          {
          var nextLayer = ogs.geo.featureLayer({
            "opacity" : 1,
            "showAttribution" : 1,
            "visible" : 1
           },
           actors[i]
          );
          myMap.addLayer(nextLayer);
          }
      }
      </script>

      <link rel="stylesheet" href="http://code.jquery.com/ui/1.10.1/themes/base/jquery-ui.css" />
      <script src="http://code.jquery.com/jquery-1.9.1.js"></script>
      <script src="http://code.jquery.com/ui/1.10.1/jquery-ui.js"></script>
    </head>
    <body onload="main()">
      <canvas id="glcanvas" width="800" height="600"></canvas>
    </body>
  </html>
""") % {'datasetString':datasetString}
        return res

    def serveVTKGeoJSON(self, datasetString):
        '''
        Deliver a geojson encoded serialized vtkpolydata file and render it
        over the canonical cpipe scene.
        '''

        if vtkOK == False:
            return """<html><head></head><body>VTK python bindings are not loadable, be sure VTK is installed on the server and its PATHS are set appropriately.</body><html>"""

        ss = vtk.vtkNetCDFCFReader() #get test data
        ss.SphericalCoordinatesOff()
        ss.SetOutputTypeToImage()
        datadir = cherrypy.request.app.config['/data']['tools.staticdir.dir']
        datadir = os.path.join(datadir, 'assets')
        datafile = os.path.join(datadir, 'clt.nc')
        ss.SetFileName(datafile)

        sf = vtk.vtkDataSetSurfaceFilter() #convert to polydata
        sf.SetInputConnection(ss.GetOutputPort())

        cf = vtk.vtkContourFilter() #add some attributes
        cf.SetInputConnection(sf.GetOutputPort())
        cf.SetInputArrayToProcess(0,0,0,"vtkDataObject::FIELD_ASSOCIATION_POINTS", "clt")
        cf.SetNumberOfContours(10)
        sf.Update()
        drange = sf.GetOutput().GetPointData().GetArray(0).GetRange()
        for x in range(0,10):
          cf.SetValue(x,x*0.1*(drange[1]-drange[0])+drange[0])
        cf.ComputeScalarsOn()

        ef = vtk.vtkExtractEdges() #make lines to test
        ef.SetInputConnection(sf.GetOutputPort())

        gf = vtk.vtkGlyph3D() #make verts to test
        pts = vtk.vtkPoints()
        pts.InsertNextPoint(0,0,0)
        verts = vtk.vtkCellArray()
        avert = vtk.vtkVertex()
        avert.GetPointIds().SetId(0, 0)
        verts.InsertNextCell(avert)
        onevertglyph = vtk.vtkPolyData()
        onevertglyph.SetPoints(pts)
        onevertglyph.SetVerts(verts)
        gf.SetSourceData(onevertglyph)
        gf.SetInputConnection(sf.GetOutputPort())

        if datasetString == "points":
            toshow = gf
        elif datasetString == "lines":
            toshow = ef
        elif datasetString == "contour":
            toshow = cf
        else:
            toshow = sf
        gw = vtk.vtkGeoJSONWriter()
        gw.SetInputConnection(toshow.GetOutputPort())
        gw.SetScalarFormat(2);
        if True:
            gw.SetFileName("/Source/CPIPES/buildogs/deploy/dataset.gj")
            gw.Write()
            f = file("/Source/CPIPES/buildogs/deploy/dataset.gj")
            gj = str(f.readlines())
        else:
            gw.WriteToOutputStringOn()
            gw.Write()
            gj = "['"+str(gw.RegisterAndGetOutputString()).replace('\n','')+"']"

        res = ("""
  <html>
    <head>
      <script type="text/javascript" src="/common/js/gl-matrix.js"></script>
      <script type="text/javascript" src="/lib/geoweb.min.js"></script>
      <script type="text/javascript" src="//ajax.googleapis.com/ajax/libs/jquery/1.9.0/jquery.min.js"></script>
      <script type="text/javascript">
      function makedata() {
        var datasetString = %(gjfile)s.join('\\n');

        var data = new ogs.vgl.geojsonReader().getPrimitives(datasetString);
        var geoms = data.geoms;

        var mapper = new ogs.vgl.mapper();
        mapper.setGeometryData(geoms[0]);
        """ +
        self.gjShader +
        """
        var actor = new ogs.vgl.actor();
        actor.setMapper(mapper);
        actor.setMaterial(mat);
        return actor;
      }
      </script>
      <script type="text/javascript">
      function main() {
        var mapOptions = {
          zoom : 1,
          center : ogs.geo.latlng(0.0, 0.0),
          source : '/data/assets/land_shallow_topo_2048.png'
        };
        var myMap = ogs.geo.map(document.getElementById("glcanvas"), mapOptions);

        var planeLayer = ogs.geo.featureLayer({
          "opacity" : 1,
          "showAttribution" : 1,
          "visible" : 1
         },
         makedata()
         );
        myMap.addLayer(planeLayer);
      }
      </script>

      <link rel="stylesheet" href="http://code.jquery.com/ui/1.10.1/themes/base/jquery-ui.css" />
      <script src="http://code.jquery.com/jquery-1.9.1.js"></script>
      <script src="http://code.jquery.com/ui/1.10.1/jquery-ui.js"></script>
    </head>
    <body onload="main()">
      <canvas id="glcanvas" width="800" height="600"></canvas>
    </body>
  </html>
""") % {'gjfile' :gj}

        return res

    def serveLUT(self):
        '''
        Test color mapping
        '''

        res = """
  <html>
    <head>
      <script type="text/javascript" src="/common/js/gl-matrix.js"></script>
      <script type="text/javascript" src="/lib/geoweb.min.js"></script>
      <script type="text/javascript" src="//ajax.googleapis.com/ajax/libs/jquery/1.9.0/jquery.min.js"></script>
      <script type="text/javascript">
      function makedata() {
        var mat = new ogs.vgl.material();

        var prog = new ogs.vgl.shaderProgram();

        var posVertAttr = new ogs.vgl.vertexAttribute("aVertexPosition");
        prog.addVertexAttribute(posVertAttr, ogs.vgl.vertexAttributeKeys.Position);

        var posScalarAttr = new ogs.vgl.vertexAttribute("aVertexScalar");
        prog.addVertexAttribute(posScalarAttr, ogs.vgl.vertexAttributeKeys.Scalar);

        var LUT0 = new ogs.vgl.floatUniform("LUT0", -1.0);
        prog.addUniform(LUT0);
        var LUT1 = new ogs.vgl.floatUniform("LUT1", 2.0);
        prog.addUniform(LUT1);

        var modelViewUniform = new ogs.vgl.modelViewUniform("modelViewMatrix");
        prog.addUniform(modelViewUniform);

        var projectionUniform = new ogs.vgl.projectionUniform("projectionMatrix");
        prog.addUniform(projectionUniform);

        //TODO: can't turn color on when not prsesent or we don't see multiX geometry
        //compare 4 and 4.c and 9 and 9.c with and without aVertexColor, could of course
        //just always produce 1,1,1 in unpack
        var vertexShaderSource = [
          'attribute vec3 aVertexPosition;',
          'attribute float aVertexScalar;',
          'uniform float LUT0, LUT1;',
          'uniform mat4 modelViewMatrix;',
          'uniform mat4 projectionMatrix;',
          'varying float vScalar;',
          'void main(void)',
          '{',
            'gl_Position = projectionMatrix * modelViewMatrix * vec4(aVertexPosition, 1.0);',
            'vScalar = (aVertexScalar-LUT0)/(LUT1-LUT0);',
          '}'
        ].join('\\n');
        var vertexShader = new ogs.vgl.shader(gl.VERTEX_SHADER);
        vertexShader.setShaderSource(vertexShaderSource);
        prog.addShader(vertexShader);

        var fragmentShaderSource = [
         'precision mediump float;',
         'varying float vScalar;',
         'uniform sampler2D sampler2d;',
         'void main(void) {',
           //'gl_FragColor = vec4(vScalar, vScalar, vScalar, 1.0);',
           'gl_FragColor = vec4(texture2D(sampler2d, vec2(vScalar, 0.0)).xyz, 1);',
         '}'
        ].join('\\n');
        var fragmentShader = new ogs.vgl.shader(gl.FRAGMENT_SHADER);
        fragmentShader.setShaderSource(fragmentShaderSource);
        prog.addShader(fragmentShader);
        mat.addAttribute(prog);

        var geom = new ogs.vgl.geometryData();
        geom.setName("LUT test data");

        /*
        var coords = new ogs.vgl.sourceData();
        coords.pushBack = function(pos, scal) {
           this.insert(pos);
           this.insert(scal);
        };
        coords.addAttribute(vertexAttributeKeys.Position, gl.FLOAT, 4, 0, 4*4, 3,
                            false);
        coords.addAttribute(vertexAttributeKeys.Scalar, gl.FLOAT, 4, 3*4, 4*4, 1,
                            false);
        coords.pushBack([-10,-10,  0], -1);
        coords.pushBack([  0,  10,  0], 0.5);
        coords.pushBack([ 10,-10,  0], 2);
        coords.pushBack([ -20, 10,  0], 2);
        geom.addSource(coords);
        */

        //
        var coords = new ogs.vgl.sourceDataP3fv();
        geom.addSource(coords);
        coords.pushBack([-10,-10,  0]);
        coords.pushBack([ 0,  10,  0]);
        coords.pushBack([10, -10,  0]);
        coords.pushBack([-20, 10,  0]);

        var scalars = new ogs.vgl.sourceData();
        scalars.addAttribute(vertexAttributeKeys.Scalar, gl.FLOAT, 4, 0, 4, 1,
                            false);
        scalars.pushBack = function(scal) {
           this.insert(scal);
        };
        geom.addSource(scalars);
        scalars.pushBack(-1);
        scalars.pushBack(0.5);
        scalars.pushBack(2);
        scalars.pushBack(2);
        //

        var indices = new Uint16Array([0,1,2]);
        var vgltriangle = new vglModule.triangles();
        vgltriangle.setIndices(indices);
        geom.addPrimitive(vgltriangle);
        var indices2 = new Uint16Array([0,1,3]);
        var vgltriangle2 = new vglModule.triangles();
        vgltriangle2.setIndices(indices2);
        //geom.addPrimitive(vgltriangle2);

        var actors = [];
        var mapper = new ogs.vgl.mapper();
        mapper.setGeometryData(geom);
        var actor = new ogs.vgl.actor();
        actor.setMapper(mapper);

        var lut = new ogs.vgl.lookupTable();
        lut.setColorTable([255,0,0,255,0,255,0,255,0,0,255,255])
        mat.addAttribute(lut);
        actor.setMaterial(mat);

        actors.push(actor);

        return actors;
      }
      </script>
      <script type="text/javascript">
      function main() {
        var mapOptions = {
          zoom : 1,
          center : ogs.geo.latlng(0.0, 0.0),
          source : '/data/assets/land_shallow_topo_2048.png'
        };
        var myMap = ogs.geo.map(document.getElementById("glcanvas"), mapOptions);
        actors = makedata();

        //TODO: change layer.js to take multiple actors
        for (var i = 0; i < actors.length; i++)
          {
          var nextLayer = ogs.geo.featureLayer({
            "opacity" : 1,
            "showAttribution" : 1,
            "visible" : 1
           },
           actors[i]
          );
          myMap.addLayer(nextLayer);
          }
      }
      </script>

      <link rel="stylesheet" href="http://code.jquery.com/ui/1.10.1/themes/base/jquery-ui.css" />
      <script src="http://code.jquery.com/jquery-1.9.1.js"></script>
      <script src="http://code.jquery.com/ui/1.10.1/jquery-ui.js"></script>
    </head>
    <body onload="main()">
      <canvas id="glcanvas" width="800" height="600"></canvas>
    </body>
  </html>
"""
        return res

    def serveCOLOR(self):
        '''
        Test color mapping
        '''

        res = """
  <html>
    <head>
      <script type="text/javascript" src="/common/js/gl-matrix.js"></script>
      <script type="text/javascript" src="/lib/geoweb.min.js"></script>
      <script type="text/javascript" src="//ajax.googleapis.com/ajax/libs/jquery/1.9.0/jquery.min.js"></script>
      <script type="text/javascript">
      function makedata() {
        var mat = new ogs.vgl.material();

        var prog = new ogs.vgl.shaderProgram();

        var posVertAttr = new ogs.vgl.vertexAttribute("aVertexPosition");
        prog.addVertexAttribute(posVertAttr, ogs.vgl.vertexAttributeKeys.Position);

        var posColorAttr = new ogs.vgl.vertexAttribute("aVertexColor");
        prog.addVertexAttribute(posColorAttr, ogs.vgl.vertexAttributeKeys.Color);

        var modelViewUniform = new ogs.vgl.modelViewUniform("modelViewMatrix");
        prog.addUniform(modelViewUniform);

        var projectionUniform = new ogs.vgl.projectionUniform("projectionMatrix");
        prog.addUniform(projectionUniform);

        var vertexShaderSource = [
          'attribute vec3 aVertexPosition;',
          'attribute vec3 aVertexColor;',
          'uniform mat4 modelViewMatrix;',
          'uniform mat4 projectionMatrix;',
          'varying vec3 vColor;',
          'void main(void)',
          '{',
            'gl_Position = projectionMatrix * modelViewMatrix * vec4(aVertexPosition, 1.0);',
            'vColor = aVertexColor;',
          '}'
        ].join('\\n');
        var vertexShader = new ogs.vgl.shader(gl.VERTEX_SHADER);
        vertexShader.setShaderSource(vertexShaderSource);
        prog.addShader(vertexShader);

        var fragmentShaderSource = [
         'precision mediump float;',
         'varying vec3 vColor;',
         'void main(void) {',
           'gl_FragColor = vec4(vColor, 1.0);',
           '}'
        ].join('\\n');
        var fragmentShader = new ogs.vgl.shader(gl.FRAGMENT_SHADER);
        fragmentShader.setShaderSource(fragmentShaderSource);
        prog.addShader(fragmentShader);
        mat.addAttribute(prog);

        var geom = new ogs.vgl.geometryData();
        geom.setName("LUT test data");

        var coords = new ogs.vgl.sourceData();
        coords.pushBack = function(pos, color) {
           this.insert(pos);
           this.insert(color);
        };

        coords.addAttribute(vertexAttributeKeys.Position, gl.FLOAT, 4, 0, 6*4, 3,
                            false);
        coords.addAttribute(vertexAttributeKeys.Color, gl.FLOAT, 4, 3*4, 6*4, 3,
                            false);
        coords.pushBack([-10,-10,  0], [1.0, 0.0, 0.0]);
        coords.pushBack([  0,  10,  0], [0.0, 1.0, 0.0]);
        coords.pushBack([ 10,-10,  0], [0.0, 0.0, 1.0]);
        coords.pushBack([ -20, 10,  0], [0.0, 0.0, 1.0]);
        geom.addSource(coords);

        var indices = new Uint16Array([0,1,2]);
        var vgltriangle = new vglModule.triangles();
        vgltriangle.setIndices(indices);
        geom.addPrimitive(vgltriangle);
        var indices2 = new Uint16Array([0,1,3]);
        var vgltriangle2 = new vglModule.triangles();
        vgltriangle2.setIndices(indices2);
        //geom.addPrimitive(vgltriangle2);

        var actors = [];
        var mapper = new ogs.vgl.mapper();
        mapper.setGeometryData(geom);
        var actor = new ogs.vgl.actor();
        actor.setMapper(mapper);

        actor.setMaterial(mat);

        actors.push(actor);

        return actors;
      }
      </script>
      <script type="text/javascript">
      function main() {
        var mapOptions = {
          zoom : 1,
          center : ogs.geo.latlng(0.0, 0.0),
          source : '/data/assets/land_shallow_topo_2048.png'
        };
        var myMap = ogs.geo.map(document.getElementById("glcanvas"), mapOptions);
        actors = makedata();

        //TODO: change layer.js to take multiple actors
        for (var i = 0; i < actors.length; i++)
          {
          var nextLayer = ogs.geo.featureLayer({
            "opacity" : 1,
            "showAttribution" : 1,
            "visible" : 1
           },
           actors[i]
          );
          myMap.addLayer(nextLayer);
          }
      }
      </script>

      <link rel="stylesheet" href="http://code.jquery.com/ui/1.10.1/themes/base/jquery-ui.css" />
      <script src="http://code.jquery.com/jquery-1.9.1.js"></script>
      <script src="http://code.jquery.com/ui/1.10.1/jquery-ui.js"></script>
    </head>
    <body onload="main()">
      <canvas id="glcanvas" width="800" height="600"></canvas>
    </body>
  </html>
"""
        return res

    @cherrypy.expose
    def index(self, which=None, datasetString="lines"):
        '''
        Entry point for web app. Ex: http://localhost:8080/vtk?which=VTK&datasetString=lines
        '''
        if which == "VTK":
          if datasetString == "lines":
            v = self.serveVTKWebGL(self.lineString)
          elif datasetString == "points":
            v = self.serveVTKWebGL(self.pointString)
          else:
            v = self.serveVTKWebGL(self.meshString)
        elif which == "GJ":
          self.geoString["points"] = self.geoString['2'];
          self.geoString["lines"] = self.geoString['4'];
          self.geoString["mesh"] = self.geoString['9'];
          string = self.geoString.get(datasetString, None);
          if (string == None):
            string = self.geoString['9.c']
          v = self.serveGeoJSON(string)
        elif which == "VTKGJ":
          v = self.serveVTKGeoJSON(datasetString)
        elif which == "LUT":
          v = self.serveLUT()
        elif which == "COLOR":
          v = self.serveCOLOR()
        else:
          v = """<html><head></head><body>""" + """
Demonstrates creating content on server, serializing it, and rendering over a map in the client.</p>
ex:</p>
To demonstrate rendering paraview webgl exporters binary encoded json:</p>
localhost:8080/vtk?which=VTK&datasetString=points</p>
localhost:8080/vtk?which=VTK&datasetString=lines</p>
localhost:8080/vtk?which=VTK&datasetString=mesh</p>
</p>
To demonstrate rendering canonical geojson data:</p>
localhost:8080/vtk?which=GJ&datasetString=points</p>
localhost:8080/vtk?which=GJ&datasetString=lines</p>
localhost:8080/vtk?which=GJ&datasetString=mesh</p>
localhost:8080/vtk?which=GJ&datasetString=N where N=1..13</p>
localhost:8080/vtk?which=GJ&datasetString=N.c same as above but with color on points</p>
</p>
To demonstrate running a vtk pipeline on the server and rendering its geojson output (requires the Geovis/IO module)</p>
localhost:8080/vtk?which=VTKGJ&datasetString=points</p>
localhost:8080/vtk?which=VTKGJ&datasetString=lines</p>
localhost:8080/vtk?which=VTKGJ&datasetString=mesh</p>
localhost:8080/vtk?which=VTKGJ&datasetString=contour</p>
</p>
To demonstrate a color lookup table</p>
localhost:8080/vtk?which=LUT</p>
localhost:8080/vtk?which=COLOR</p>

""" + """
</body><html>"""
        return v
