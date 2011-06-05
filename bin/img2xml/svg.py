# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="hcayless"
__date__ ="$Aug 24, 2010 9:56:46 AM$"

if __name__ == "__main__":
    print "Hello World"
    
from lxml import etree
import re
import numpy

class SVG:

  def __init__(self, doc):
    self.doc = doc
    self.nss = {'svg': 'http://www.w3.org/2000/svg'}
    self.SVG_NS = "http://www.w3.org/2000/svg"
    self.XLINK_NS = "http://www.w3.org/1999/xlink"
    self.NS = "{%s}" % self.SVG_NS
    self.XLNS = "{%s}" % self.XLINK_NS
    self.NSMAP = {None: self.SVG_NS}

  def getwidth(self):
    '''Gets the document width.'''
    svg = self.doc.xpath("/svg:svg", namespaces=self.nss)[0]
    return int(svg.attrib.get("width").rstrip("pt"))

  def getheight(self):
    '''Gets the document height.'''
    svg = self.doc.xpath("/svg:svg", namespaces=self.nss)[0]
    return int(svg.attrib.get("height").rstrip("pt"))

  def getviewbox(self):
    '''Gets the dimensions of the document\' viewbox.'''
    svg = self.doc.xpath("/svg:svg", namespaces=self.nss)[0]
    return svg.attrib.get("viewBox").split(" ")

  def getxmin(self):
    '''Gets the lower X bound of the document.'''
    result = self.getviewbox()
    return int(result[0])

  def getymin(self):
    '''Gets the lower Y bound of the document.'''
    result = self.getviewbox()
    return int(result[1])

  def add_rectangle(self, rect, fill, opacity):
    '''Adds an svg:rect with the supplied characteristics.'''
    style = "fill:%s;fill-opacity:1;opacity:%s" % (fill, opacity)
    self.doc.getroot().append(etree.Element(self.NS + "rect", x=str(rect.tl.x), y=str(rect.tl.y), width=str(rect.width()), height=str(rect.height()), id=rect.id, style=style,  nsmap=self.NSMAP))

  def add_group(self, group):
    pg = self.doc.xpath("/svg:svg/svg:g", namespaces=self.nss)[0]
    g = etree.SubElement(pg, self.NS + "g", id="g%s" % group.id, nsmap=self.NSMAP)
    for path in group.shapes:
      id = "%s" % path.id[1:]
      xpath = "//svg:path[@id='%s']" % id
      p = self.doc.xpath(xpath, namespaces=self.nss)[0]
      pg.remove(p)
      g.append(p)

  def ungroup(self):
    '''Since potrace wraps all svg:paths in an svg:g, this function unwraps them
    and converts their path data to the document\s coordinate system.'''
    g = self.doc.xpath("/svg:svg/svg:g", namespaces=self.nss)[0]
    for path in g.xpath("svg:path", namespaces=self.nss):
      g.remove(path)
      path.attrib['d'] = self.transformpath(path.attrib['d'])
      self.doc.getroot().append(path)
    self.doc.getroot().remove(g)

  def add_image(self, url):
    '''Adds a background image to the SVG document.'''
    width = self.doc.xpath("//svg:svg/@width", namespaces=self.nss)[0].rstrip("pt")
    height = self.doc.xpath("//svg:svg/@height", namespaces=self.nss)[0].rstrip("pt")
    image = etree.Element(self.NS + "image", nsmap={None: self.SVG_NS, "xlink": self.XLINK_NS})
    image.set(self.XLNS + "href", url)
    image.set(self.XLNS + "actuate", "onLoad")
    image.set("width", width)
    image.set("height", height)
    self.doc.getroot().insert(0, image)

  def getmatrices(self):
    '''Returns a numpy matrix derived from the svg:g element\'s @transform attribute.'''
    if False == hasattr(self, "matrices"):
      self.matrices = {}
      g = self.doc.xpath("/svg:svg/svg:g", namespaces=self.nss)
      if g:
        t = g[0].get("transform")
        if t:
          transforms = t.split(" ")
          fm = False
          #print transforms
          for f in transforms:
            if f.find("matrix") >= 0:
              #print "Found matrix"
              m = f.lstrip("matrix(").rstrip(")")
              m = m.split(",")
              self.matrices['matrix'] = numpy.matrix( [[float(m[0]),float(m[2]),float(m[4])],[float(m[1]),float(m[3]),float(m[5])],[0,0,1]])
              continue
            if f.find("translate") >= 0:
              #print "Found translate"
              l = f.lstrip("translate(").rstrip(")")
              translate = l.split(",")
              self.matrices['translate'] = numpy.matrix([[1,0,float(translate[0])],[0,1,float(translate[1])],[0,0,1]])
              continue
            if f.find("scale") >= 0:
              #print "Found scale"
              s = f.lstrip("scale(").rstrip(")")
              scale = s.split(",")
              self.matrices['scale'] = numpy.matrix([[float(scale[0]),0,0],[0,float(scale[1]),0],[0,0,1]])
              continue
    if len(self.matrices) == 0:
      self.matrices['matrix'] = numpy.matrix([[1,0,0],[0,1,0],[0,0,1]])
    return self.matrices

  def getpathbyid(self, id):
    '''Returns a the svg:path with the supplied id.'''
    return self.doc.xpath("//svg:path[@id='%s']" % (id), namespaces=self.nss)

  def getpathdata(self):
    '''Gets the path information in the svg:path/@d attribute.'''
    paths = self.doc.xpath("//svg:path", namespaces=self.nss)
    result = []
    for path in paths:
      result.append((path.get('id'), path.get('d')))
    return result

  def getrects(self):
    '''Retrieves a list of Rectangles based on the <svg:rect> elements in the document.'''
    rects = self.doc.xpath("//svg:rect", namespaces=self.nss)
    result = []
    for r in rects:
      x = float(r.get('x'))
      y = float(r.get('y'))
      w = float(r.get('width'))
      h = float(r.get('height'))
      result.append(Rectangle({'tl':(x, y), 'tr':(x, y+w), 'bl':(x+h, y), 'br':(x+h, y+w), 'id':r.get('id')}))
    return result

  def transformpath(self, path):
    '''Used in removing paths from an svg:g container. Converts the 
    supplied path to the document\'s coordinate system.'''
    points = path.split()
    result = ""
    pt = ""
    tf = "all"
    for point in points:
      if pt == "":
        pt = point
      else:
        if point.isalpha():
          pt += " %s" % point
        else:
          pt += point
      if not pt.isalpha():
        if pt[0].isalpha():
          result += " %s" % pt[0]
          if pt[0].islower():
            function = "scale"
          else:
            function = "all"
          pt = pt[1:]
        if pt.find(",") > 0:
          if pt[len(pt) - 1].isalpha():
            p = self.transformpoint(pt[0:len(pt) - 1], function)
            result += " %s,%s" % p
            result += pt[len(pt) - 1]
          else:
            p = self.transformpoint(pt, function)
            result += " %s,%s " % p
          pt = ""
        else:
          pt += ","
      else:
        result += " %s" % point
        if pt.islower():
          function = "scale"
        else:
          function = "all"
    return result

  def transformpoint(self, point, function="all"):
    '''applies the supplied function (scale, translate, or all) to the given point 
    using the matrices extracted from the containing group.'''
    p = point.split(",")
    tp = numpy.matrix( [[float(p[0])], [float(p[1])], [1]])
    matrices = self.getmatrices()
    
    if (function == "scale" or function == "all") and matrices.has_key('scale'):
      tp = matrices['scale'] * tp
    if (function == "translate" or function == "all") and matrices.has_key('translate'):
      tp = matrices['translate'] * tp
    if function == "all" and matrices.has_key('matrix'):
      tp = matrices['matrix'] * tp
    return (float(tp[0]), float(tp[1]))

  def absolute_coords(self, coords, current):
    '''Converts relative coordinates to absolute.'''
    pair = coords.split(",")
    cpair = current.split(",")
    pair[0] = str(float(pair[0]) + float(cpair[0]))
    pair[1] = str(float(pair[1]) + float(cpair[1]))
    return ",".join(pair)

  # returns a list of path information
  def analysepaths(self):
    '''Analyses all of the svg:paths in the document and returns a list of bounding polygons.'''
    polygons = []
    pcount = 0
    for pathdata in self.doc.xpath("//svg:path", namespaces=self.nss):
      pcount = pcount + 1
      path = pathdata.xpath("@d")[0].replace("\n", ' ').split()
      index = 0
      polygon = []
      current = ""
      start = ""
      for p in path:
        if p.find('m') == 0:
          if "" != start:
            current = start
          if p != 'm':
            if index == 0:
              pair = "%s,%s" % (p.lstrip('m'), path[index + 1])
              polygon.append(pair)
              current = pair
              start = current
          else:
            if index == 0:
              current = path[index + 1]
            else:
              current = self.absolute_coords(path[index + 1], current)
            start = current
            polygon.append(current)
        if p.find('M') == 0:
          if p != 'M':
            pair = "%s,%s" % (p.lstrip('M'), path[index + 1])
            current = pair
          else:
            current = path[index + 1]
          start = current
          polygon.append(current)
        if p.find('l') == 0:
          if p != 'l':
            pair = "%s,%s" % (p.lstrip('l'), path[index + 1])
            current = self.absolute_coords(pair, current)
            polygon.append(current)
          else:
            i = index
            while re.match("[-.0-9]+,[-.0-9z]+", path[i+1]):
              current = self.absolute_coords(path[i + 1].rstrip('z'), current)
              polygon.append(current)
              if path[i+1].find('z') > 0:
                break
              i = i + 1
        if p.find('L') == 0:
          if p != 'L':
            pair = "%s,%s" % (p.lstrip('L'), path[index + 1])
            current = pair
          else:
            current = path[index + 1]
          polygon.append(current)
        if p.find('c') == 0:
          if p != 'c':
            pair = "%s,%s" % (p.lstrip('c'), path[index + 1])
            current = self.absolute_coords(pair, current)
            polygon.append(current)
            i = index + 2
            while path[i].isdigit():
              c2 = path[i + 1]
              if c2.find('z') > 0:
                pair = "%s,%s" % (path[i], c2.rstrip('z'))
              else :
                pair = "%s,%s" % (path[i], c2)
              current = self.absolute_coords(pair, current)
              polygon.append(current)
              if c2.find('z') > 0:
                break
              i = i + 2
          else:
            i = index + 1
            c = 0
            while re.match("[-.0-9]+,[-.0-9z]+", path[i]):
              if c == 2:
                current = self.absolute_coords(path[i].rstrip('z'), current)
                polygon.append(current)
                if path[i].find('z') > 0:
                  break
                c = 0
              else:
                polygon.append(self.absolute_coords(path[i].rstrip('z'), current))
                c = c + 1
              i = i + 1
        if p.find('C') == 0:
          if p != 'C':
            pair = "%s,%s" % (p.lstrip('C'), path[index + 1])
            polygon.append(pair)
            pair = "%s,%s" % (path[index + 2], path[index + 3])
            polygon.append(pair)
            pair = "%s,%s" % (path[index + 4], path[index + 5])
            current = pair
            polygon.append(current)
          else:
            polygon.append(path[index + 1])
            polygon.append(path[index + 2])
            current = path[index + 3]
            polygon.append(current)
        index = index + 1
      pid = pathdata.xpath("@id")
      if not(pid):
        pid = "p%s" % str(pcount).rjust(5, "0")
      polygons.append((pid[0], polygon))
    return polygons