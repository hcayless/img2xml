<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:svg="http://www.w3.org/2000/svg"
  version="1.0">
  
  <!-- Converts svg:rects in the source document into OpenLayers vector features. -->
  
  <xsl:output method="text"/>
  
  <xsl:variable name="height" select="translate(//svg:svg/@height, 'pt', '')"/>
  
  <xsl:template match="/">
    var rectsLayer = new OpenLayers.Layer.Vector("Lines");
    var rectFeatures = new Array();
    <xsl:apply-templates select="//svg:rect"/>
    rectsLayer.addFeatures(rectFeatures);
    map.addLayer(rectsLayer);
  </xsl:template>
  
  <xsl:template match="svg:rect">
    <xsl:variable name="bottom" select="round($height - @y)"/>
    <xsl:variable name="top" select="round($bottom - @height)"/>
    var <xsl:value-of select="@id"/> = new OpenLayers.Feature.Vector(new OpenLayers.Bounds(<xsl:value-of select="@x"/>, <xsl:value-of select="$bottom"/>, <xsl:value-of select="@width"/>, <xsl:value-of select="$top"/>).toGeometry(), {name:'<xsl:value-of select="@id"/>'}, {fill:false,stroke:false});
    rectFeatures.push(<xsl:value-of select="@id"/>);</xsl:template>
  
</xsl:stylesheet>