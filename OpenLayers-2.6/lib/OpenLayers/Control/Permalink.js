/* Copyright (c) 2006-2008 MetaCarta, Inc., published under the Clear BSD
 * license.  See http://svn.openlayers.org/trunk/openlayers/license.txt for the
 * full text of the license. */


/**
 * @requires OpenLayers/Control.js
 */

/**
 * Class: OpenLayers.Control.Permalink
 * 
 * Inherits from:
 *  - <OpenLayers.Control>
 */
OpenLayers.Control.Permalink = OpenLayers.Class(OpenLayers.Control, {

    /** 
     * Property: element 
     * {DOMElement}
     */
    element: null,
    
    /** 
     * APIProperty: base
     * {String}
     */
    base: '',

    /** 
     * APIProperty: displayProjection
     * {<OpenLayers.Projection>} Requires proj4js support.  Projection used
     *     when creating the coordinates in the link. This will reproject the
     *     map coordinates into display coordinates. If you are using this
     *     functionality, the permalink which is last added to the map will
     *     determine the coordinate type which is read from the URL, which
     *     means you should not add permalinks with different
     *     displayProjections to the same map. 
     */
    displayProjection: null, 

    /**
     * Constructor: OpenLayers.Control.Permalink
     *
     * Parameters: 
     * element - {DOMElement} 
     * base - {String} 
     * options - {Object} options to the control. 
     */
    initialize: function(element, base, options) {
        OpenLayers.Control.prototype.initialize.apply(this, [options]);
        this.element = OpenLayers.Util.getElement(element);        
        this.base = base || document.location.href;
    },

    /**
     * APIMethod: destroy
     */
    destroy: function()  {
        if (this.element.parentNode == this.div) {
            this.div.removeChild(this.element);
        }
        this.element = null;

        this.map.events.unregister('moveend', this, this.updateLink);

        OpenLayers.Control.prototype.destroy.apply(this, arguments); 
    },

    /**
     * Method: setMap
     * Set the map property for the control. 
     * 
     * Parameters:
     * map - {<OpenLayers.Map>} 
     */
    setMap: function(map) {
        OpenLayers.Control.prototype.setMap.apply(this, arguments);

        //make sure we have an arg parser attached
        for(var i=0; i< this.map.controls.length; i++) {
            var control = this.map.controls[i];
            if (control.CLASS_NAME == "OpenLayers.Control.ArgParser") {
                
                // If a permalink is added to the map, and an ArgParser already
                // exists, we override the displayProjection to be the one
                // on the permalink. 
                if (control.displayProjection != this.displayProjection) {
                    this.displayProjection = control.displayProjection;
                }    
                
                break;
            }
        }
        if (i == this.map.controls.length) {
            this.map.addControl(new OpenLayers.Control.ArgParser(
                { 'displayProjection': this.displayProjection }));       
        }

    },

    /**
     * Method: draw
     *
     * Returns:
     * {DOMElement}
     */    
    draw: function() {
        OpenLayers.Control.prototype.draw.apply(this, arguments);
          
        if (!this.element) {
            this.element = document.createElement("a");
            this.element.innerHTML = OpenLayers.i18n("permalink");
            this.element.href="";
            this.div.appendChild(this.element);
        }
        this.map.events.on({
            'moveend': this.updateLink,
            'changelayer': this.updateLink,
            'changebaselayer': this.updateLink,
            scope: this
        });
        return this.div;
    },
   
    /**
     * Method: updateLink 
     */
    updateLink: function() {
        var center = this.map.getCenter();
        
        // Map not initialized yet. Break out of this function.
        if (!center) { 
            return; 
        }

        var params = OpenLayers.Util.getParameters(this.base);
        
        params.zoom = this.map.getZoom(); 
        var lat = center.lat;
        var lon = center.lon;
        
        if (this.displayProjection) {
            var mapPosition = OpenLayers.Projection.transform(
              { x: lon, y: lat }, 
              this.map.getProjectionObject(), 
              this.displayProjection );
            lon = mapPosition.x;  
            lat = mapPosition.y;  
        }       
        params.lat = Math.round(lat*100000)/100000;
        params.lon = Math.round(lon*100000)/100000;
        
        params.layers = '';
        for(var i=0; i< this.map.layers.length; i++) {
            var layer = this.map.layers[i];

            if (layer.isBaseLayer) {
                params.layers += (layer == this.map.baseLayer) ? "B" : "0";
            } else {
                params.layers += (layer.getVisibility()) ? "T" : "F";           
            }
        }

        var href = this.base;
        if( href.indexOf('?') != -1 ){
            href = href.substring( 0, href.indexOf('?') );
        }

        href += '?' + OpenLayers.Util.getParameterString(params);
        this.element.href = href;
    }, 

    CLASS_NAME: "OpenLayers.Control.Permalink"
});
