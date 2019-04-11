  // Localize & shorthand django vars
  var l = window.harvard_md_server;

  var hMirador = Mirador.viewer({
    "id": "viewer",
    "windows": [ l.MIRADOR_WOBJECTS ],
    "manifests": {}
  });

  var ftype_alias = {
    'ImageView': 'i',
    'BookView': 'b',
    'ScrollView': 's',
    'ThumbnailsView': 't'
  };

  var constructUrl = function (omit_id) {
    var object_ids = $.map(hMirador.viewer.workspace.slots, function (slot, i) {
      var mirWindow = slot.window;
      if (mirWindow) {
        var uri = mirWindow.manifest.uri,
            parts = uri.split("/"),
            last_idx = parts.length - 1,
	    drs_match = parts[last_idx].match(/drs:(\d+)/),
            drs_id = drs_match && drs_match[1],
            focusType = mirWindow.currentFocus,
            n = mirWindow.focusModules[focusType].currentImgIndex + 1;
        if (mirWindow.id === omit_id) {
          //pass
        }
        else if (drs_match) {
          return 'drs:' + drs_id + '$' + n + ftype_alias[focusType];
        }
        else {
          return "ext:" + Base64.encode(uri).replace(/\+/g, '-').replace(/\//g, '_') + '$' + n + ftype_alias[focusType];
        }
      }
    });
    return object_ids.join(";");
  };
