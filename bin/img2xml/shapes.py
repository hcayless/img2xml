# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="hcayless"
__date__ ="$Aug 24, 2010 9:53:58 AM$"

if __name__ == "__main__":
    print "Hello World"

import numpy

class Point:
  '''Defines a point.'''
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def string(self):
    '''Gets the point coordinates as a string.'''
    return "%s,%s" % (self.x, self.y)

  def isbetween(self, pt1, pt2, d):
    '''Determines whether this point is between point 1 and point 2 in a given dimension.'''
    dim1 = getattr(pt1, d)
    dim2 = getattr(pt2, d)
    dim = getattr(self, d)
    if dim1 <= dim2:
      return dim1 <= dim <= dim2
    else:
      return dim1 >= dim >= dim2

class Rectangle:
  '''Defines a rectangle.'''
  def __init__(self, rect=None):
    self.id = None
    self.tr = None
    self.tl = None
    self.br = None
    self.bl = None
    self.avgh = None
    if rect != None:
      self.tr = Point(float(rect['tr'][0]), float(rect['tr'][1]))
      self.tl = Point(float(rect['tl'][0]), float(rect['tl'][1]))
      self.br = Point(float(rect['br'][0]), float(rect['br'][1]))
      self.bl = Point(float(rect['bl'][0]), float(rect['bl'][1]))
      if 'id' in rect:
        self.id = (rect['id'])

  def height(self):
    '''Gets the rectangle\'s height.'''
    return self.br.y - self.tr.y

  def width(self):
    '''Gets the rectangle\'s width.'''
    return self.tr.x - self.tl.x

  def area(self):
    '''Gets the rectangle\'s area.'''
    return self.height() * self.width()

  def string(self):
    '''Gets the coordinates of the rectangle\'s corners as a string.'''
    return "%s %s %s %s" % (self.tl.string(), self.tr.string(), self.br.string(), self.bl.string())

  def intersects(self, rect):
    '''Determines whether this rectangle intersects with the supplied one.'''
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
    '''Determines whether the supplied point is inside this rectangle.'''
    if hasattr(point, 'x'):
      return (self.tl.x <= point.x <= self.br.x) & (self.tl.y <= point.y <= self.br.y)
    else:
      return self.contains(self.tl) and self.contains(self.tr) and self.contains(self.bl) and self.contains(self.br)

  def verticaloverlap(self, rect):
    '''Gets the degree of vertical overlap between this and the supplied rectangle as a percentage.'''
    result = ((numpy.min((self.br.y, rect.br.y)) - numpy.max((self.tr.y, rect.tr.y))) / numpy.min((self.height(), rect.height()))) * 100.0
    if result < 0.0:
      result = 0.0
    if result > 100.0:
      result = 100.0
    return result
  
  def merge(self, rect):
    '''Merges the supplied rectangle with the current one to produce a larger rectangle.'''
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

  # merge the rectangle horizontally only
  def mergehoriz(self, rect):
    tl1 = self.tl
    tl2 = rect.tl
    br1 = self.br
    br2 = rect.br
    top = float(self.tl.y)
    bottom = float(self.br.y)
    left = float(tl1.x)
    if left > float(tl2.x):
      left = float(tl2.x)
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

  def midpoint(self, rect=None):
    if not rect:
      rect = self
    x = (float(rect.tr.x) + float(rect.bl.x)) / 2
    y = (float(rect.bl.y) + float(rect.tr.y)) / 2
    return Point(x,y)

class Group:
  def __init__(self, id):
    self.id = id
    self.shapes = []
    self.boundingrect = Rectangle()
    self.boundingrect.id = "r%s" % id

  # if merge is false, then only merge the new rectangle horizontally
  # this helps compensate for connected lines
  def add(self, rect, merge=True):
    self.shapes.append(rect)
    if merge:
      self.boundingrect.merge(rect)
    else:
      self.boundingrect.mergehoriz(rect)