<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns="http://www.w3.org/2000/svg"
  xmlns:svg="http://www.w3.org/2000/svg"
  xmlns:i="http://philomousos.com/img2xml/ns"
  version="2.0">
  
  <!-- Changes the coordinate system of the source SVG to the width and height provided.
          The XSLT takes two parameters, width and height (i.e. the original image's width x height.  
          For convenience's sake, I recommend processing them from the command line, using the 
          Saxon HE processor and ImageMagick's identify command.  A BASH script like the 
          following will make this process easier:
      
              for f in $(ls *.svg) 
              do 
              t=`echo $f | sed 's/svg/tif/'`
              java -jar saxon9he.jar -s:$f -xsl:/path/to/scale-svg.xsl -o:/path/to/output/$f `identify -format "width=%[fx:w] height=%[fx:h]" /path/to/source-TIFFs/$t` 
              done
  -->
  
  <xsl:param name="width"/>
  <xsl:param name="height"/>
  <xsl:variable name="scale" select="i:get-ratio(replace(/svg:svg/@width, '\D', ''))"/>
  
  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>
  
  <xsl:template match="node()|@*|comment()|processing-instruction()">
    <xsl:copy>
      <xsl:apply-templates select="node()|@*|comment()|processing-instruction()"/>
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="svg:svg">
    <xsl:copy>
      <xsl:copy-of select="@version"/>
      <xsl:copy-of select="@preserveAspectRatio"/>
      <xsl:attribute name="width" select="$width"/>
      <xsl:attribute name="height" select="$height"/>
      <xsl:attribute name="viewBox">0 0 <xsl:value-of select="$width"/><xsl:text> </xsl:text><xsl:value-of select="$height"/></xsl:attribute>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="svg:path">
    <xsl:copy>
      <xsl:copy-of select="@id"/>
      <xsl:attribute name="d">
        <xsl:for-each select="tokenize(@d, '\s')">
          <xsl:choose>
            <xsl:when test="matches(., '-*\d+\.\d*,-*\d+\.\d*')">
              <xsl:for-each select="tokenize(., ',')"><xsl:value-of select="i:round(number(.) * $scale)"/><xsl:if test="position() != last()">,</xsl:if></xsl:for-each></xsl:when>
            <xsl:otherwise><xsl:value-of select="."/></xsl:otherwise>
          </xsl:choose>
          <xsl:if test="position() != last()"><xsl:text> </xsl:text></xsl:if>
        </xsl:for-each>  
      </xsl:attribute>
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="svg:rect">
    <xsl:copy>
      <xsl:copy-of select="@id"/>
      <xsl:copy-of select="@style"/>
      <xsl:attribute name="height"><xsl:value-of select="i:round(@height * $scale)"/></xsl:attribute>
      <xsl:attribute name="width"><xsl:value-of select="i:round(@width * $scale)"/></xsl:attribute>
      <xsl:attribute name="y"><xsl:value-of select="i:round(@y * $scale)"/></xsl:attribute>
      <xsl:attribute name="x"><xsl:value-of select="i:round(@x * $scale)"/></xsl:attribute>
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="svg:g[@transform]">
    <xsl:variable name="transform">
      <xsl:analyze-string select="@transform" regex="(-?\d?\.?\d+)">
        <xsl:matching-substring><xsl:value-of select="number(regex-group(1)) * $scale"/></xsl:matching-substring>
        <xsl:non-matching-substring><xsl:value-of select="."/></xsl:non-matching-substring>
      </xsl:analyze-string>
    </xsl:variable>
    <g transform="{$transform}">
      <xsl:apply-templates/>
    </g>
  </xsl:template>
  
  <xsl:function name="i:get-ratio">
    <xsl:param name="doc-width"/>
    <xsl:variable name="scale-w" select="($width div number($doc-width))"/>
    <xsl:sequence select="$scale-w"/>
  </xsl:function>
  
  <xsl:function name="i:round">
    <xsl:param name="num"/>
    <xsl:sequence select="round($num * 1000000) div 1000000"/>
  </xsl:function>
  
</xsl:stylesheet>