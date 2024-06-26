var DownloadButton = {
  /* the template for the image urls */
  imageUrlTemplate: Mirador.Handlebars.compile(
    '{{imageBaseUrl}}/full/{{size}},/0/default.jpg?download&caption'
  ),

  /* the template for the link button */
  buttonTemplate: Mirador.Handlebars.compile([
    '<span class="mirador-btn mirador-icon-download" role="button" title="Download" aria-label="Download">',
    '<a href="javascript:;"><i class="fa fa-download fa-lg fa-fw"></i>',
    '<i class="fa fa-caret-down"></i></a>',
    '<ul class="dropdown download-list">',
    '{{#each imageUrls}}',
    '<li class="{{#if (eq this "#")}}disabled {{/if}}image-link" title="Download entire image as jpeg ({{this.sizeLabel}})" id="{{this.id}}">',
    '<a href="{{this.href}}">',
    '<i class="fa fa-file-image-o fa-lg fa-fw"></i>{{this.sizeLabel}}: <span class="dimensions">{{this.title}}</span> px',
    '</a></li>',
    '{{/each}}',
    '<li title="Download IIIF manifest in JSON format"><a href="{{manifestUrl}}" target="_blank">',
    '<i class="fa fa-file-text-o fa-lg fa-fw"></i>IIIF Manifest',
    '</a></li>',
    '</ul>',
    '</span>'
  ].join('')),

  /* extracts image urls from the viewer window */
  extractImageUrls: function(viewerWindow){
    var currentImage = viewerWindow.imagesList[viewerWindow.focusModules['ImageView'].currentImgIndex];
    var imageBaseUrl = Mirador.Iiif.getImageUrl(currentImage);
    var ratio = currentImage.height / currentImage.width;
    var currentImageId = imageBaseUrl.split("/").pop().split(":").pop();

    var imageInfoUrl = imageBaseUrl + "/info.json";


   var sizeLabels = { 300 : 'Small', 800 : 'Medium', 1200 : 'Large', 2400 :'X-Large' };
   var maxWidth = 2400;
   var maxHeight = 2400;
   var req = new XMLHttpRequest();
   req.overrideMimeType("application/json");
   req.open('GET', imageInfoUrl, true);
   req.onload  = function() {
   	var jsonResponse = JSON.parse(req.responseText);
	var sizes = jsonResponse["sizes"];
	maxHeight = jsonResponse["maxHeight"];
	maxWidth = jsonResponse["maxWidth"];
	
	var sizes = [300,800,1200,2400];
	for(var i=0, len=sizes.length; i < len; i++){
	  size = sizes[i];
	  var scaledHeight = Math.ceil(size * ratio);
	  id = "#download_" + size.toString();
          if ( (size > maxWidth) && (scaledHeight > maxHeight)) {
	    $(id).addClass('disabled');
          } else {
	    $(id).removeClass('disabled');
	  }
	}

   };
   req.send(null);

    var imageUrls = [];
    //['full', '250,'].forEach(function(size){
    ['300','800','1200','2400'].forEach(function(size){
	var sHeight = Math.ceil(parseInt(size) * ratio);
	var sizeVal = parseInt(size);
	var iiifUrl = imageBaseUrl;
	if ((sizeVal > maxWidth) && (sHeight > maxHeight)) {
	  sizeVal = "";
	  iiifUrl = "";
	} 
        imageUrls.push({
            'href': viewerWindow.currentImageMode !== 'ImageView' ? '#' : this.imageUrlTemplate({
            'imageBaseUrl': iiifUrl, 'size': sizeVal
            }),
            'title': size === 'full' ? currentImage.width + 'x' + currentImage.height : parseInt(size) + ' x ' + sHeight,
            'sizeLabel': sizeLabels[parseInt(size)], 'id': "download_" + parseInt(size)
         });
    }.bind(this));

    return imageUrls;


  },

  /* initializes the plugin, i.e. adds an event handler */
  init: function(){
    Mirador.Handlebars.registerHelper('eq', function(first, second){
      return first === second;
    });
    this.injectWindowEventHandler();
    this.injectWorkspaceEventHandler();
  },

  /* injects the button to the window menu */
  injectButtonToMenu: function(windowButtons, manifestUrl, imageUrls){
    $(windowButtons).prepend(this.buttonTemplate({
      'imageUrls': imageUrls,
      'manifestUrl': manifestUrl,
    }));
  },

  /* injects the needed window event handler */
  injectWindowEventHandler: function(){
    var this_ = this;
    var origBindNavigation = Mirador.Window.prototype.bindNavigation;
    Mirador.Window.prototype.bindNavigation = function(){
      origBindNavigation.apply(this);
      this.element.find('.window-manifest-navigation').on(
        'mouseenter', '.mirador-icon-download', function(){
          this.element.find('.download-list').stop().slideFadeToggle(300);
        }.bind(this)
      ).on(
        'mouseleave', '.mirador-icon-download', function(){
          this.element.find('.download-list').stop().slideFadeToggle(300);
        }.bind(this)
      );
    };
    var origBindEvents = Mirador.Window.prototype.bindEvents;
    Mirador.Window.prototype.bindEvents = function(){
      origBindEvents.apply(this);
      this.eventEmitter.subscribe('windowUpdated', function(evt, data){
        if(this.id !== data.id || !data.viewType){
          return;
        }
        if(data.viewType === 'ImageView'){
          var imageUrls = this_.extractImageUrls(this);
          this.element.find('.image-link').removeClass('disabled').attr(
            'title', function(index){ return 'JPG (' + imageUrls[index].title + ')'; }
          ).find('a').attr(
            'href', function(index){ return imageUrls[index].href; }
          ).find('span.dimensions').text(
            function(index){ return imageUrls[index].title; }
          );
        }else{
          this.element.find('.image-link').addClass('disabled');
        }
      }.bind(this));
    };
  },

  /* injects the needed workspace event handler */
  injectWorkspaceEventHandler: function(){
    var this_ = this;
    var origFunc = Mirador.Workspace.prototype.bindEvents;
    Mirador.Workspace.prototype.bindEvents = function(){
      origFunc.apply(this);
      this.eventEmitter.subscribe('windowAdded', function(evt, data){
        var viewerWindow = this.windows.filter(function(currentWindow){
          return currentWindow.id === data.id;
        })[0];
        var manifestUrl = viewerWindow.manifest.jsonLd['@id'];
        var canvases = viewerWindow.manifest.jsonLd.sequences[0].canvases;
        var imageUrls = this_.extractImageUrls(viewerWindow);
        var windowButtons = viewerWindow.element.find('.window-manifest-navigation');
        this_.injectButtonToMenu(windowButtons, manifestUrl, imageUrls);
	this.eventEmitter.publish('downloadPluginAdded', viewerWindow.id);
      }.bind(this));
    };
  }
};

$(document).ready(function(){
  DownloadButton.init();
});
