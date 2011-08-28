img2xml
======

img2xml is a toolchain for linking images of text to transcriptions and annotations. A working demo may be seen at (http://docsouth.unc.edu/dusenbery).

1. Source TIFFs may need to be pre-processed to removed dark margins, using select/fill in a standard image editor, such as Photoshop or the Gimp.  These processed TIFFs are converted to bitmaps, using ImageMagick's convert tool, with a BASH command like:
	
	convert image.tif image.pnm
	
or in batch with a command like:

	for f in $(ls *.tif); do convert $f ``echo $f | sed 's/\([^.]*\).tif/\1.pnm/'``; done
	
2. they are then traced using [potrace](http://potrace.sourceforge.net/):

	potrace -s -k 0.6 image.pnm
	
which will produce an SVG file, image.svg.  Batch commands may be used, like:

	for f in $(ls *.pnm); do potrace -s -k 0.6 $f; done
	
The '-k N' parameter may be varied between 0 and 1 if the results are undesirable.  The 'k' parameter represents the black/white cutoff and may have to be adjusted for images where the surface is darker, or the ink lighter, etc.

3. Once the SVGs have been created, line detection can be performed using the Python script in the bin/ directory. The script is executed in the following way:

	python line_detector.py input.svg output.svg
	
The result will be an SVG with the paths (representing a tracing of the source image's text) ungrouped, and the lines of text wrapped in svg:rect shapes.  These should be checked, and if necessary corrected manually, using an SVG editor like Inkscape.

4. Once the SVG tracings, with lines detected, have been QA-ed, they should be scaled and corrected using a pair of stylesheets.  /xslt/scale-svg.xsl scales the SVG's coordinate system to match that of the source image.  The XSLT takes two parameters, width and height.  For convenience's sake, I recommend processing them from the command line, using the Saxon HE processor, which may be obtained from http://saxon.sourceforge.net/.  A BASH script like the following will make this process easier:
	
	for f in $(ls *.svg) 
	do 
	t=`echo $f | sed 's/svg/tif/'`
	java -jar ~/Development/saxonhe9-2-0-2j/saxon9he.jar -s:$f -xsl:../scale-svg.xsl -o:../diary_pages_scaled/$f `identify -format "width=%[fx:w] height=%[fx:h]" ../diary_pages_altered/$t` 
	done
	
(where we assume the script is being run in the directory containing the SVG files, the output is going into a parallel directory, 'diary_pages_scaled', and the TIFFs are in another parallel directory, 'diary_pages_altered'.).

If any edits have been made to the SVG in Inkscape that involve the addition of new line rects or the deletion of superfluous ones, the xslt/order-rects.xsl stylesheet will clean these up.  The journal application expects lines to have sequential @ids like, "line1, line2", etc..

5. Finally, the SVG lines are converted to OpenLayers features using xslt/svg-to-js.xsl.  The resulting .js files go in static/journal/images/pages/.
