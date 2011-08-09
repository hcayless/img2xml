<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:s="http://www.w3.org/2000/svg"
                xmlns="http://www.w3.org/2000/svg"
                version="2.0">
  
  <!-- Processes SVG files with added svg:rect shapes denoting lines to make certain
          that the svg:rects are in order, top-to-bottom, with ids in ascending order.-->
  
  <xsl:output indent="yes"/>
  
  <xsl:template match="/">
      <xsl:apply-templates select="*[local-name(.) != 'rect']"/>
  </xsl:template>
  
  <xsl:template match="s:svg">
      <xsl:variable name="rects">
         <xsl:apply-templates select="s:rect">
            <xsl:sort select="@y" data-type="number"/>
         </xsl:apply-templates>
      </xsl:variable>
      <xsl:copy>
         <xsl:apply-templates select="*[local-name(.) != 'rect']|@*"/>
         <xsl:for-each select="$rects/s:rect">
            <xsl:copy>
               <xsl:copy-of select="@*[not(local-name(.) = 'id')]"/>
               <xsl:attribute name="id">line<xsl:value-of select="count(preceding-sibling::s:rect) + 1"/>
               </xsl:attribute>
            </xsl:copy>
         </xsl:for-each>
      </xsl:copy>
  </xsl:template>
  
  <xsl:template match="s:rect">
      <xsl:copy-of select="."/>
  </xsl:template>
  
  <xsl:template match="node()|@*">
      <xsl:copy>
         <xsl:apply-templates select="node()|@*"/>
      </xsl:copy>
  </xsl:template>
  
</xsl:stylesheet>