(function() {
  var originalWindowInit = Mirador.Window.prototype.init;

  var template = Mirador.Handlebars.compile([
    '<label class="mirador-select-jump-label">Jump to: </label><select class="{{selectClassName}}" aria-label="Jump to page">',
    '{{#canvases}}',
    '<option value="{{id}}">{{label}}</option>',
    '{{/canvases}}',
    '</select>'
  ].join(''));

  Mirador.Window.prototype.init = function(){
    var windowObj = this;

    originalWindowInit.apply(windowObj);

    var canvases = windowObj.imagesList.map(function(canvas){
      canvas.id = canvas['@id'];
      return canvas;
    });

   
    windowObj.eventEmitter.subscribe('downloadPluginAdded', function(evt, data){

      windowObj.element.find('.window-manifest-navigation').prepend(template({
        'selectClassName': 'mirador-select-jump page-select', 
        'canvases': canvases
      }));

      windowObj.element.find('.page-select').on('change', function(event) {
        var canvasID = jQuery(this).val();
        windowObj.eventEmitter.publish('SET_CURRENT_CANVAS_ID.' + windowObj.id, canvasID);
      });

   });

  };
})();
