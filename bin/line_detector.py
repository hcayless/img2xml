import os.path
import os
#! /usr/bin/python

# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="hcayless"
__date__ ="$Aug 30, 2010 9:57:10 PM$"

import sys
from lxml import etree
import math
import numpy
# img2xml code
import img2xml.shapes
import img2xml.svg

# Constants
# Depending on the handwriting style, assumptions about line height may
# need to be adjusted below.
line_height_below = 3
line_height_above = 2


def count_objects(rectangles, svg, avg):
  '''Returns a dictionary with counts of shapes per unit on the Y axis in the SVG.'''
  count = dict.fromkeys(range(svg.getymin(), svg.getymin() + svg.getheight()), 0)
  for r in rectangles[0:]:
    for p in range(int(r.tr.y), int(r.br.y)):
      if (r.area() >= avg):
        if p in count:
          count[p] = count[p] + 1
        else:
          count[p] = 1
  return count

def getvalues(range, dict):
  '''Returns a list of values in the dictionary for the given range.'''
  result = []
  for k in range:
    result.append(dict[k])
  return result

def detect_lines(counts, svg, h):
  '''Performs line detection by looking at peaks in the supplied dictionary, and then
  appends line-bounding rectangles to the supplied SVG.'''
  result = {}
  start = numpy.min(counts.keys())
  i = start
  avg = 0
  peaks = []
  peakindex = 0
  up = True
  # 'h' is a rough average height for objects, so expect it to be about the height of an 'e'.
  while i < (numpy.max(counts.keys()) - (h + 1)):
    localavg = numpy.average(getvalues(range(i,i + h), counts))
    if up:
      if localavg > avg:
        avg = localavg
      else:
        if avg > localavg + 0.1:
          peaks.append(i - 1)
          peakindex = peakindex + 1
          up = False
    else:
      if avg > localavg:
        avg = localavg
      else:
        if localavg > avg:
          up = True
    i = i + 1
  idno = 1
  lines = []
  rpeaks = []
  i = 1
  previous = 2
  rpeaks.append(peaks[0])
  for p in peaks:
    if i >= 2:  
      if peaks[i - previous] < p - (h * line_height_below):
        rpeaks.append(p)
        previous = 2
      else:
        previous = 3
      i = i + 1
    else:
      i = i + 1
    
  peaks = rpeaks
  for p in peaks:
    id = "line%s" % idno
    idno = idno + 1
    # draw line-bounding rectangle
    rect = img2xml.shapes.Rectangle({'tr':(svg.getxmin() + svg.getwidth(),p - (h * line_height_above)),'tl':(svg.getxmin(),p - (h * line_height_above)),'br':(svg.getxmin() + svg.getwidth(),p + (h * line_height_below)),'bl':(svg.getxmin(),p + (h * line_height_below)),'id':id})
    lines.append(rect)

  for line in lines:
    svg.add_rectangle(line, "#0000ff", "0.5")
    
  return svg

def extract_rectangle(polygon):
  '''Given a polygon, return the bounding rectangle'''
  #print polygon
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
  rectangle = img2xml.shapes.Rectangle({'tr': tr, 'tl': tl, 'br': br, 'bl': bl})
  return rectangle

def main():
  file = sys.argv[1]
  out = sys.argv[2]
  doc = etree.parse(file)
  s = img2xml.svg.SVG(doc)
  s.ungroup()

  polygons = s.analysepaths()

  rectangles = []
  areas = []
  heights = []
  for poly in polygons:
    rect = extract_rectangle(poly[1])
    rect.id = "r" + poly[0]
    rectangles.append(rect)
    areas.append(rect.area())
    heights.append(rect.height())
  lines = count_objects(rectangles, s, numpy.average(areas))
  s = detect_lines(lines, s, int(round(numpy.average(heights))))
  f = open(out, 'w')
  f.write(etree.tostring(s.doc))
  f.close()



if __name__ == "__main__":
    sys.exit(main())


