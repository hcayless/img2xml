#!/usr/bin/env python
# encoding: utf-8
"""
getrectangles.py

Created by Hugh Cayless on 2008-07-25.
Copyright (c) 2008 Hugh A. Cayless

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
.
"""

import sys
import getopt
from lxml import etree
import numpy
import subprocess

help_message = '''
The help message goes here.
'''

class Point:
  def __init__(self, x, y):
    self.x = x
    self.y = y
    
  def string(self):
    return "%s,%s" % (self.x, self.y)
    
  def isbetween(self, pt1, pt2, d):
    dim1 = getattr(pt1, d)
    dim2 = getattr(pt2, d)
    dim = getattr(self, d)
    if dim1 <= dim2:
      return dim1 <= dim <= dim2
    else:
      return dim1 >= dim >= dim2

class Rectangle:
  def __init__(self, rect=None):
    self.id = None
    self.tr = None
    self.tl = None
    self.br = None
    self.bl = None
    if rect != None:
      self.tr = Point(float(rect['tr'][0]), float(rect['tr'][1]))
      self.tl = Point(float(rect['tl'][0]), float(rect['tl'][1]))
      self.br = Point(float(rect['br'][0]), float(rect['br'][1]))
      self.bl = Point(float(rect['bl'][0]), float(rect['bl'][1]))
   
  def height(self):
    return self.br.y - self.tr.y
    
  def width(self):
    return self.tr.x - self.tl.x
  
  def string(self):
    return "%s %s %s %s" % (self.tl.string(), self.tr.string(), self.br.string(), self.bl.string())
    
  def intersects(self, rect):
    if self.contains(rect.tl):
      return True
    if self.contains(rect.tr):
      return True
    if self.contains(rect.bl):
      return True
    if self.contains(rect.br):
      return True
    return False
    
  def contains(self, point):
    #print "%s <= %s <= %s & %s <= %s <= %s" % (self.tl.x, point.x, self.br.x, self.tl.y, point.y, self.br.y)
    return (self.tl.x <= point.x <= self.br.x) & (self.tl.y <= point.y <= self.br.y)
    
  def verticaloverlap(self, rect):
    result = ((numpy.min((self.br.y, rect.br.y)) - numpy.max((self.tr.y, rect.tr.y))) / numpy.min((self.height(), rect.height()))) * 100.0
    if result < 0.0:
      result = 0.0
    if result > 100.0:
      result = 100.0
    return result
  
  def merge(self, rect):
    if self.tr == None:
      self.tl = rect.tl
      self.tr = rect.tr
      self.bl = rect.bl
      self.br = rect.br
    else:
      tl1 = self.tl
      tl2 = rect.tl
      br1 = self.br
      br2 = rect.br
      top = float(tl1.y)
      if top > float(tl2.y):
        top = float(tl2.y)
      left = float(tl1.x)
      if left > float(tl2.x):
        left = float(tl2.x)
      bottom = float(br1.y)
      if bottom < float(br2.y):
        bottom = float(br2.y)
      right = float(br1.x)
      if right < float(br2.x):
        right = float(br2.x)
      self.tr = Point(right, top)
      self.tl = Point(left, top)
      self.br = Point(right, bottom)
      self.bl = Point(left, bottom)
      
  def transform(self, matrix):
    r = Rectangle()
    tr = matrix * numpy.matrix([[self.tr.x], [self.tr.y], [1]])
    r.tr = Point(float(tr[0]),float(tr[1]))
    tl = matrix * (numpy.matrix([[self.tl.x], [self.tl.y], [1]]))
    r.tl = Point(float(tl[0]),float(tl[1]))
    br = matrix * (numpy.matrix([[self.br.x], [self.br.y], [1]]))
    r.br = Point(float(br[0]),float(br[1]))
    bl = matrix * (numpy.matrix([[self.bl.x], [self.bl.y], [1]]))
    r.bl = Point(float(bl[0]),float(bl[1]))
    return r
    
class Group:
  def __init__(self, id):
    self.id = id
    self.shapes = []
    self.boundingrect = Rectangle()
    self.boundingrect.id = "r%s" % id
    
  def add(self, rect):
    self.shapes.append(rect)
    self.boundingrect.merge(rect)

class SVG:
  
  def __init__(self, doc):
    self.doc = doc
    self.nss = {'svg': 'http://www.w3.org/2000/svg'}
    self.SVG_NS = "http://www.w3.org/2000/svg"
    self.XLINK_NS = "http://www.w3.org/1999/xlink"
    self.NS = "{%s}" % self.SVG_NS
    self.XLNS = "{%s}" % self.XLINK_NS
    self.NSMAP = {None: self.SVG_NS}
    
  def add_rectangle(self, rect, fill, opacity):
    r = rect.transform(self.getmatrix())
    self.doc.getroot().append(etree.Element(self.NS + "polygon", points=r.string(), id=rect.id, fill=fill, opacity=opacity, stroke="blue",  nsmap=self.NSMAP))
    
  def add_group(self, group):
    pg = self.doc.xpath("/svg:svg/svg:g", namespaces=self.nss)[0]
    g = etree.SubElement(pg, self.NS + "g", id="g%s" % group.id, nsmap=self.NSMAP)
    for path in group.shapes:
      id = "%s" % path.id[1:]
      xpath = "//svg:path[@id='%s']" % id
      p = self.doc.xpath(xpath, namespaces=self.nss)[0]
      pg.remove(p)
      g.append(p)
  
  def add_image(self, url):
    width = self.doc.xpath("//svg:svg/@width", namespaces=self.nss)[0].rstrip("pt")
    height = self.doc.xpath("//svg:svg/@height", namespaces=self.nss)[0].rstrip("pt")
    image = etree.Element(self.NS + "image", nsmap={None: self.SVG_NS, "xlink": self.XLINK_NS})
    image.set(self.XLNS + "href", url)
    image.set(self.XLNS + "actuate", "onLoad")
    image.set("width", width)
    image.set("height", height)
    self.doc.getroot().insert(0, image)
    
  def add_hline(self, y, start, end):
    self.doc.xpath("/svg:svg/svg:g", namespaces=self.nss)[0].end(etree.Element(self.NS + "line", x1=start, x2=end, y1=y, y2=y, stroke="red", nsmap=self.NSMAP))
    
  def getmatrix(self):
    if False == hasattr(self, "matrix"):
      g = self.doc.xpath("/svg:svg/svg:g", namespaces=self.nss)[0]
      t = g.get("transform").lstrip("matrix()").rstrip(")")
      t = t.split(",")
      self.matrix = numpy.matrix( [[float(t[0]),float(t[2]),float(t[4])],[float(t[1]),float(t[3]),float(t[5])],[0,0,1]])
      print self.matrix
    return self.matrix
    
  def getpathbyid(self, id):
    return self.doc.xpath("//svg:g/svg:path[@id='%s']" % (id), namespaces=self.nss)
    
  def getpathdata(self):
    paths = self.doc.xpath("//svg:g/svg:path", namespaces=self.nss)
    result = []
    for path in paths:
      result.append((path.get('id'), path.get('d')))
    return result
    
  def transformpath(self, path):
    points = path.split(" ")
    result = ""
    s = self.getmatrix()
    for point in points:
      if not point.isalpha():
        p = point.split(",")
        matrix = numpy.matrix( [[float(p[0])], [float(p[1])], [1]])
        tp = s * matrix
        result += " %s,%s " % ((float(tp[0])), (float(tp[1])))
      else:
        result += point
    return result
    
class JS:
  
  def __init__(self, svg):
    self.svg = svg
    self.nss = {'svg': 'http://www.w3.org/2000/svg'}
    self.SVG_NS = "http://www.w3.org/2000/svg"
    self.XLINK_NS = "http://www.w3.org/1999/xlink"
    self.NS = "{%s}" % self.SVG_NS
    self.XLNS = "{%s}" % self.XLINK_NS
    self.NSMAP = {None: self.SVG_NS}
  
  def writejs(self, out, img, rects, groups):
    js = '''
    var map;
    function init(){
      
      OpenLayers.Feature.Vector.style['default']['fillOpacity'] = '0.2';
      OpenLayers.Feature.Vector.style['default']['strokeWidth'] = '2';
      OpenLayers.Feature.Vector.style['select']['fillOpacity'] = '0.0';
      
        map = new OpenLayers.Map('page');
        //map.addControl(new OpenLayers.Control.MousePosition());


        var options = {numZoomLevels: 3};

        var graphic = new OpenLayers.Layer.Image(
                            'Page Image',
    '''
    js += "'files/%s'," % img
    js += '''
                            new OpenLayers.Bounds(-55.375, -81, 55.375, 81  ),
                            new OpenLayers.Size(443, 648),
                            options);

        var rectsLayer = new OpenLayers.Layer.Vector("Lines");
        var rectFeatures = new Array();
    '''
    for i in range(len(rects)):
      js += "     var rect%s = new OpenLayers.Feature.Vector(new OpenLayers.Bounds((%s/4)-56.125, -((%s/4)-81), (%s/4)-56.125, -((%s/4) - 81)).toGeometry(), {id:'%s'});\n" % (i, rects[i].bl.x, rects[i].bl.y, rects[i].tr.x, rects[i].tr.y, rects[i].id)
      js += "     rectFeatures[%s] = rect%s;\n" % (i,i)
    js += '''
        rectsLayer.addFeatures(rectFeatures);
        
        var layer_style = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        layer_style.fillOpacity = "0.3";
        layer_style.fillColor = "black"
        layer_style.strokeWidth = "0";
        
        var pathsLayer = new OpenLayers.Layer.Vector("Paths", {style: layer_style});
        var pathFeatures = new Array();
    '''
    #paths = self.svg.getpathdata()
    #for i in range(len(paths)):
    #  js += "     var path%s = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Path('%s', {id:'%s'}));\n" % (i, self.svg.transformpath(paths[i][1]), paths[i][0])
    #  js += "     pathFeatures[%s] = path%s;\n" % (i,i)
    #
    for i in range(len(groups)):
      js += "        var paths = new Array();\n"
      for r in groups[i].shapes:
        path = self.svg.getpathbyid(r.id.lstrip('rgw'))
        js += "       path%s = new OpenLayers.Geometry.Path('%s', {id:'%s'});\n" % (path[0].get('id'), self.svg.transformpath(path[0].get('d')), path[0].get('id'))
        js += "       paths.push(path%s);\n" % (path[0].get('id'))
      js += "        var pg%s = new OpenLayers.Geometry.PathGroup(paths,'%s');\n" % (i, groups[i].id)
      js += "        var g%s = new OpenLayers.Feature.Vector(pg%s);\n" % (i,i)
      js += "        pathFeatures[%s] = g%s;\n" % (i,i)
    js += '''
        pathsLayer.addFeatures(pathFeatures);
        
        map.addLayers([graphic, pathsLayer, rectsLayer]);
        var select = new OpenLayers.Control.SelectFeature(
            rectsLayer,
            {
                clickout: false,
                hover: true,
                onSelect: function(f) {
                  var g = $("#"+f.attributes.id);
                  g.attr("fill","red");
                  g.attr("fill-opacity", "1");
                  g.attr("stroke-width","0.5");
                  g.attr("stroke-color", "red");
                  var ids = eval("img2xml."+f.attributes.id);
                  for (i=0; i < ids.length; i++) {
                    $("#"+ids[i]).css({fontWeight:"bold",fontSize:"1.2em"});
                  }
                },
                onUnselect: function(f) {
                  var g = $("#"+f.attributes.id);
                  g.attr("fill","black");
                  g.attr("fill-opacity", "0.3");
                  g.attr("stroke-width","0");
                  var ids = eval("img2xml."+f.attributes.id);
                  for (i=0; i < ids.length; i++) {
                    $("#"+ids[i]).css({fontWeight:"normal",fontSize:"1em"});
                  }
                }
            }
        );
        
        map.addControl(select);
        select.activate();
        map.addControl(new OpenLayers.Control.LayerSwitcher());
        map.zoomToMaxExtent();
    }
    '''
    f = open(out, 'w')
    f.write(js);
    f.close

class Usage(Exception):
  def __init__(self, msg):
    self.msg = msg

def extract_rectangle(polygon):
  pair = polygon[0].split(',')
  left = float(pair[0])
  right = left
  top = float(pair[1])
  bottom = top
  for p in polygon:
    pair = p.split(',')
    x = float(pair[0])
    y = float(pair[1])
    if x < left:
      left = x
    if x > right:
      right = x
    if y < top:
      top = y
    if y > bottom:
      bottom = y

  tr = (right, top)
  tl = (left, top)
  br = (right,bottom)
  bl = (left,bottom)
  rectangle = Rectangle({'tr': tr, 'tl': tl, 'br': br, 'bl': bl})
  return rectangle
  
def midpoint(rect):
  x = (float(rect.tr.x) + float(rect.bl.x)) / 2
  y = (float(rect.bl.y) + float(rect.tr.y)) / 2
  return Point(x,y)

def get_area(rect):
  h = float(rect.bl.y) - float(rect.tr.y)
  w = float(rect.tr.x) - float(rect.bl.x)
  return w * h
  
def getheight(rect):
  return float(rect.bl.y) - float(rect.tr.y)

# sorts a list of rectangles
def sort(list, dim):
  if list == []: 
      return []
  else:
    pivot = list[0]
    lesser = sort([rect for rect in list[1:] if getattr(rect.tl, dim) < getattr(pivot.tl, dim)], dim)
    greater = sort([rect for rect in list[1:] if getattr(rect.tl, dim) >= getattr(pivot.tl, dim)], dim)
    return lesser + [pivot] + greater
    
# sorts a list of groups 
def groupsort(list, dim):
  if list == []: 
      return []
  else:
    pivot = list[0]
    lesser = groupsort([g for g in list[1:] if getattr(g.boundingrect.tl, dim) < getattr(pivot.boundingrect.tl, dim)], dim)
    greater = groupsort([g for g in list[1:] if getattr(g.boundingrect.tl, dim) >= getattr(pivot.boundingrect.tl, dim)], dim)
    return lesser + [pivot] + greater

def filter_rectangles(list, lower, upper):
  result = []
  for item in list:
    area = get_area(item)
    if (area >= lower) & (area <= upper):
      result.append(item)
  return result
  
def filter_groups(list, lower, upper):
    result = []
    for item in list:
      area = getheight(item.boundingrect)
      if (area >= lower) & (area <= upper):
        result.append(item)
    return result
  
def get_lines(rectangles, result, overlap):
  rect = rectangles[0]
  remainder = []
  group = Group("g%s" % rect.id)
  group.add(rect)
  for r in rectangles[1:]:
    if group.boundingrect.verticaloverlap(r) > overlap:
      group.add(r)
    else:
      remainder.append(r)
  result.append(group)
  if (len(remainder) > 0) & (len(remainder) < len(rectangles)):
    get_lines(remainder, result, overlap)
  
def get_words(rects, result):
  rect = rects[0]
  remainder = []
  group = Group("w%s" % rect.id)
  group.add(rect)
  for r in rects[1:]:
    if (group.boundingrect.intersects(r) & (group.boundingrect.verticaloverlap(r) > 50.0)):
      group.add(r)
    else:
      remainder.append(r)
  result.append(group)
  if (len(remainder) > 0) & (len(remainder) < len(rects)):
    get_words(remainder, result)

# compute areas
# throw out outliers
# use tl
# sort top to bottom, left to right
# start at 0 find all that overlap (significantly?) in series
# merge rectangles, add to lines array
# start again at next non-overlapping rect
  

def main(argv=None):
  if argv is None:
    argv = sys.argv
  try:
    try:
      opts, args = getopt.getopt(argv[1:], "ho:i:v", ["help", "output=", "image="])
    except getopt.error, msg:
      raise Usage(msg)
  
    print opts
    print args
    # option processing
    for option, value in opts:
      if option == "-v":
        verbose = True
      if option in ("-h", "--help"):
        raise Usage(help_message)
      if option in ("-o", "--output"):
        output = value
      if option in ("-i", "--image"):
        image = value
    
    
    
    file = args[0]
    if not 'output' in locals():
      output = file
    svg = etree.parse(file)
    s = SVG(svg)
    polygons = []
    for pathdata in svg.xpath("//svg:path", namespaces={'svg': 'http://www.w3.org/2000/svg'}):
      path = pathdata.xpath("@d")[0].split(' ')
      index = 0
      polygon = []
      for p in path:
        if p == 'M':
          polygon.append(path[index + 1])
        if p == 'L':
          polygon.append(path[index + 1])
        if p == 'C':
          polygon.append(path[index + 1])
          polygon.append(path[index + 2])
          polygon.append(path[index + 3])
        index = index + 1
      polygons.append((pathdata.xpath("@id")[0], polygon))
      
    rectangles = []
    areas = []
    for poly in polygons:
      rect = extract_rectangle(poly[1])
      rect.id = "r" + poly[0]
      rectangles.append(rect)
      areas.append(get_area(rect))
    print numpy.max(areas)
    print numpy.min(areas)
    print numpy.average(areas)
    print numpy.std(areas)
    #print areas
    #print rectangles
    
    rectangles = filter_rectangles(rectangles, (numpy.average(areas) - (2 *numpy.std(areas))), numpy.max(areas) - 1  )
    #rectangles = filter_rectangles(rectangles, (numpy.average(areas) - (10 * numpy.std(areas))), numpy.max(areas)  )
    rectangles = sort(rectangles, 'x')
    rectangles = sort(rectangles, 'y')
    areas = []
    for rect in rectangles:
      areas.append(get_area(rect))

    lines = []
    get_lines(rectangles, lines, 50.0)
    
    heights = []
    for group in lines:
      heights.append(getheight(group.boundingrect))
    print "Group Areas:"
    print numpy.min(heights)
    print numpy.average(heights)
    print numpy.std(heights)
    #lines = filter_groups(lines, (numpy.average(heights) + (numpy.std(heights))), numpy.max(heights))
    lines = filter_groups(lines, (numpy.average(heights) - (numpy.std(heights))), numpy.max(heights))
    
    rects = []
    for group in lines:
      r = group.boundingrect.transform(s.getmatrix())
      r.id = group.id
      rects.append(r)
    js = JS(s)
    js.writejs("%s.js" % output, image, rects, lines)
    
    #write SVG
    lines = groupsort(lines,'y')
    for group in lines:
      s.add_rectangle(group.boundingrect, 'yellow', '0.3')
      s.add_group(group)
      #s.add_hline("%s" % group.baseline(), "%s" % group.boundingrect.tl.x, "%s" % group.boundingrect.tr.x)
      #words = []
      #shapes = sort(group.shapes, 'x')
      #get_words(shapes, words)
      #for word in words:
      #  s.add_rectangle(word.boundingrect, 'green', '0.2')
        
    s.add_image(image)
    f = open(output, 'w')
    f.write(etree.tostring(s.doc))
    f.close()
    #print etree.tostring(s.doc)
        
    
  except Usage, err:
    print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
    print >> sys.stderr, "\t for help use --help"
    return 2


if __name__ == "__main__":
  sys.exit(main())
