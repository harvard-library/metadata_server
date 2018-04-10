var hMirador;
$(function() {
  // Localize & shorthand django vars
  var l = window.harvard_md_server;

  var dialogBaseOpts = {
    modal: true,
    draggable: false,
    resizable: false,
    width: "50%",
    closeText: null,
    classes: "qtip-bootstrap",
    close: function (e) { $(this).remove()}
  };

  //Handlebars comparison handler for related links filtering
  Handlebars.registerHelper('isLink', function (link, options) {
    var isLink = link.toLowerCase().indexOf('http') > -1 ? true : false;
    if (isLink)
      return options.fn(this);
    else
      return options.inverse(this);
  });

  // Compile Handlebars templates into t
  var t = {};
  $('script[type="text/x-handlebars-template"]').each(function () {
    t[this.id] = Handlebars.compile(this.innerHTML);
  });

  //print form
  var validateEmail = function(email) {
    var re = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
    return re.test(email);
   }

  var printPDF = function(e){
    e.preventDefault();
    var d_id = $("#drs_id").val();
    var img_id = $("#img_id").val();
    var url = "/proxy/printpdf/" + d_id;
    var xmlhttp;
    var n = $("#n").val();
    if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
      xmlhttp=new XMLHttpRequest();
    }
    else {// code for IE6, IE5
      xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }

    var print_slot_idx = $("#print_slot_idx").val();
    var totalSeq = hMirador.viewer.workspace.slots[print_slot_idx].window.imagesList.length;


    var printMode = $('input[name=printOpt]:checked', '#printpds').val();
    var email = $("#email").val();
    var start = $("#start").val();
    var end = $("#end").val();
    var emailValid =  validateEmail(email);


    if (printMode === "current") {
      url = url + '?n=' + n +'&printOpt=single';
      window.open(url,'');
    } else if (printMode === "range") {
      if ((parseInt(start) > parseInt(end)) || (start === '') || (end ==='') || (parseInt(start) < 1) || (parseInt(end) > totalSeq)){
        $('#printmsg').css('color', '#A51C30');
        $('#printmsg').html('<b>Please select a page sequence range between 1-' + totalSeq + ' pages.</b>');
        return;
      } else if ( ((end - start) >= 10)  && (!emailValid) ){
        $('#printmsg').css('color', '#A51C30');
        $('#printmsg').html('<b>Please limit your page sequence range to a maximum of 10 pages for instant printing or enter your email address to have your larger selection sent to you.</b>');
        return;
      } 
      if ((end - start) >= 10) {
        url = url + '?printOpt=range' + '&start=' + start +
          '&end=' + end + '&email=' + email;
        xmlhttp.open('GET',url,true);
        xmlhttp.send();
        $('#printmsg').css('color', 'black');
        $('#printmsg').html('PDF sent to ' + email);
      } else {
        url = url + '?printOpt=range' + '&start=' + start + '&end=' + end + '&email=';
        window.open(url,'');
      }
    } else if (printMode == "caption")  {
      window.open(l.IDS_VIEW_URL + img_id + '?usecap=yes');
    } else  { //all
      if (totalSeq >= 10) {
        if (emailValid) {
          url = url + '?printOpt=all&email=' + email;
          xmlhttp.open('GET',url,true);
          xmlhttp.send();
          $('#printmsg').css('color', 'black');
          $('#printmsg').html('PDF sent to ' + email);
        } else {
          $('#printmsg').css('color', '#A51C30');
          $('#printmsg').html('<b>Invalid email address</b>');;
          return;
        }
      } else {
        url = url + '?printOpt=range&start=1&end=' + totalSeq + '&email=' + email;
        window.open(url,'');
      }
    }
    //$('#print-modal').dialog('close');
  };


  hMirador = Mirador({
    "id": "viewer",
    "layout": l.LAYOUT,
    "saveSession": false,
    "mainMenuSettings" : {
      "buttons": {
         bookmark: false,
	fullScreenViewer: false
      },
      "userButtons": [
	{"label": "View in PDS",
         "iconClass": "fa fa-external-link",
         "attributes": { "class": "view-in-pds", "href": "#no-op"}},
	{"label": "Search",
         "iconClass": "fa fa-search",
         "attributes": { "class": "search", "href": "#no-op"}},
	{"label": "View Text",
         "iconClass": "fa fa-font",
         "attributes": { "class": "viewtext", "href": "#no-op"}},
	{"label": "Print/Save",
         "iconClass": "fa fa-print",
         "attributes": { "class": "print", "href": "#no-op"}},
        {"label": "Cite",
         "iconClass": "fa fa-quote-left",
         "attributes": { "class": "cite", "href": "#no-op"}},
	{"label": "Related Links",
         "iconClass": "fa fa-link",
         "attributes": { "class": "links", "href": "#no-op"}},
	{"label": "Help",
         "iconClass": "fa fa-question-circle",
         "attributes": { "class": "help", "href": "#no-op"}}
      ],
    	"userLogo": {
        "label": "Harvard Library",
        "attributes": { "id": "harvard-bug", "href": "http://lib.harvard.edu"}}
    },
    "i18nPath": l.PATH_DATA.i18nPath,
    "logosLocation": l.PATH_DATA.logosLocation,
    "data": l.MIRADOR_DATA,
    "windowObjects": l.MIRADOR_WOBJECTS
  });

  setTimeout(function(){
    $('.user-buttons').slicknav({
      label: 'Menu',
      prependTo: '.mirador-main-menu-bar'
    });
  }, 3000);

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

  var present_choices = function (e) {
    e.preventDefault();
    $('.user-buttons').slicknav('close');
    var op = e.currentTarget.className.replace(/\s/g, '');
    var choices = $.map(hMirador.viewer.workspace.slots, function (slot, i) {
      var mirWindow = slot.window;
      var mirSlotID = slot.slotID;
      if (mirWindow) {
        var uri = mirWindow.manifest.uri,
            parts = uri.split("/"),
            last_idx = parts.length - 1,
	    drs_match = parts[last_idx].match(/drs:(\d+)/),
            drs_id = drs_match && drs_match[1],
            focusType = mirWindow.currentImageMode,
            n = mirWindow.focusModules[focusType].currentImgIndex + 1;
        if (drs_match) {
          return {"label": mirWindow.manifest.jsonLd.label, "drs_id": drs_id,
                  "uri": mirWindow.manifest.uri, "n": n, "slotID": mirSlotID, "slot_idx": i};
        }
        // else omit manifest because we don't know how to cite/view it
      }

    });

    if (choices.length == 1) {
      operations[op](choices[0].drs_id, choices[0].n, choices[0].slot_idx);
    } else if (choices.length == 0) {
      var $error = $('#error-modal');
      if ($error.get().length > 0) {
        $error.dialog('close');
      }
      $error = $('<div id="error-modal" style="display:none" />');
      $error.html(t['error-tmpl']({ op: "error", text: "This function is not available for non-DRS objects." }));
      $error.appendTo('body');
      $error
        .dialog($.extend({title: 'Function Unavailable'}, dialogBaseOpts))
        .dialog('open');
    }
    else {
      var $dialog = $('#choice-modal');
      if ($dialog.get().length > 0) {
        $dialog.dialog('close');
      }
      else if (choices.length) {
        $dialog = $('<div id="choice-modal" style="display:none" />');
        $dialog.html(t['choices-tmpl']({choices: choices, op: op}));
        $dialog.appendTo('body');
        $dialog.dialog($.extend({title: "Citation"}, dialogBaseOpts)).dialog('open');
        $dialog.find('a').on('click', function (e) {
          e.preventDefault();
          $dialog.dialog('close');
          operations[op]($(e.currentTarget).data('drs-id'), $(e.currentTarget).data('n'),
            $(e.currentTarget).data('slot-idx'));
        });
      }
    }
  };

  var display_help = function(e) {
    window.open("http://nrs.harvard.edu/urn-3:hul.ois:hlviewerhelp","mirador_help");
  };

  var operations = {
    "view-in-pds": function (drs_id, n, slot_idx) {
      //window.open(l.PDS_VIEW_URL + drs_id + "?n=" + n + "&oldpds");
      window.location.assign(l.PDS_VIEW_URL + drs_id + "?n=" + n + "&oldpds");
    },
    "cite": function (drs_id, n, slot_idx) {
      var $dialog = $('#citation-modal');

      if ($dialog.get().length > 0) {
        $dialog.dialog('close');
      }
      else {
        $dialog = $('<div id="citation-modal" style="display:none" />');
        $.getJSON( '/proxy/cite/' + drs_id + '?callback=?',  {'n':n} )
          .done(function (data) {
            if (data.citation) {
              $dialog.html(t['citation-tmpl'](data.citation));
              $dialog.appendTo('body');
              $dialog
                .dialog($.extend({title: "Citation"}, dialogBaseOpts))
                .dialog('open');
            } //TODO: Else graceful error display
          });
      }
    },
    "search": function(drs_id, n, slot_idx) {
      var has_ocr = false;
      //first check to see if page has text
      $.getJSON( '/proxy/hasocr/' + drs_id + '?callback=?', {'n':n})
         .done( function(data) {
          if (data.hasocr) {
             has_ocr = true;
          }
        //}); //TODO: Else graceful error display
        if (has_ocr) {
          var cSlot = hMirador.viewer.workspace.slots[slot_idx];
          var cWindow = cSlot.window;
          var citLabel = cWindow.manifest.jsonLd.label;
          var content = { drs_id: drs_id, n: n, slot_idx: slot_idx, label: citLabel, fts_view_url: l.FTS_VIEW_URL };
          var $dialog = $('#search-modal');
          if ($dialog.get().length > 0) {
            $dialog.dialog('close');
          }
          else {
            $dialog = $('<div id="search-modal" style="display:none" />');
            $dialog.html(t['search-tmpl'](content));
            $dialog
              .dialog($.extend({title: "Search"}, dialogBaseOpts))
              .dialog('open');

            //init search grid and data sources

            //data source for jq dataadapter
            var fts_source = {
              datatype: "xml",
              datafields: [
                { name: 'label', map: 'displayLabel', type: 'string'},
                { name: 'uri', map: 'deliveryUri', type: 'string'},
                { name: 'context', map: 'context', type: 'string'}
              ],
              root: "resultSet",
              record: "result"
              //pager
            };

            //adapter for search form
            var dataAdapter = new $.jqx.dataAdapter(fts_source, {
              autoBind: false,
              beforeSend: function (xhr) {
                 xhr.cache = false;
                 $('#loading').show();
              },
              loadComplete: function() {
                 $('#loading').hide();
              }
            });

            //search hitlist
            $("#hitlist").jqxListBox(
             { source: dataAdapter,
              displayMember: "context",
              valueMember: "uri",
              width: '95%',
              height: 200,
              renderer: function (index, label, value) {
                var record = dataAdapter.records[index];
                if (record != null) {
                    var sequence = parseInt((record.uri.split("="))[1]);
                    sequence = sequence - 1;
                    var curr_slot_idx = $("#current_slot_idx").val();
                    var currSlot = hMirador.viewer.workspace.slots[curr_slot_idx];
                    var currWindow = currSlot.window;
                    var thumbUrl = currWindow.imagesList[sequence].images[0].resource.service['@id'];
                    thumbUrl = thumbUrl + "/full/150,/0/native.jpg";
                    var cell = "<div style='text-align:left; float:left;'><img src='" + thumbUrl +
                      "' style='float:left' width='80' height='80' hspace='4' /> <i>" + label + "</i><br>" + record.context +
                      "<br>" + record.uri + "</div>";
                    return cell;
                }
                return "";
              }

            });

            $("#hitlist").on('bindingComplete', function (event) {
              if ( dataAdapter.records.length > 0) {
                $('#hits').html("<b>" + dataAdapter.records.length + "</b> Search Results Found");
                $('#nohits').hide();
                $('#hits').show();
                $('#hitlist').show();
              } else {
                $('#hits').hide();
                $('#hits').text('');
                $('#hitlist').hide();
                $('#nohits').show();
              }
            });


            var clearSearch = function () {
              $("#searchbox").val('');
              $('#hitlist').jqxListBox('clear');
              $('#hitlist').hide();
              $('#nohits').hide();
            };

            //handler for select -> move to mirador window
            $("#hitlist").on('select', function (event) {
              var curr_slot_idx = $("#current_slot_idx").val();
              if (event.args) {
                var item = event.args.item;
                if (item) {
                    var record = dataAdapter.records[item.index];
                    var sequence = parseInt((record.uri.split("="))[1]);
                    sequence = sequence - 1;
                    clearSearch();
                    $('#search-modal').dialog('close');
                    // TODO - jump active mirador window to this new sequence
                    var currSlot = hMirador.viewer.workspace.slots[curr_slot_idx];
                    var currWindow = currSlot.window;
                    var newCanvasID = currWindow.imagesList[sequence]['@id'];
                    currWindow.setCurrentCanvasID(newCanvasID);
                    //update panels with current image
                    if (currWindow.bottomPanel) { currWindow.bottomPanel.updateFocusImages(currWindow.focusImages); }
                    //currWindow.updatePanelsAndOverlay();
                }
              }
            });

            //handler for automatic search on keyup event in search box
            var me = this;
            $("#searchbox").on("keypress", function (event) {
              if(event.which === 13){
                 fts_source.url = "/proxy/find/" + $("#search_drs_id").val() +
                    "?Q=" + $("#searchbox").val() + "&P=100&O=" + $('input[name=searchOpt]:checked').val();
                  if (me.timer) clearTimeout(me.timer);
                  me.timer = setTimeout(function () {
                  dataAdapter.dataBind();
                 }, 300);
             }
            });

            //handler for search button
            var me2 = this;
            $("#searchbutton").on("click", function (event) {
               fts_source.url = "/proxy/find/" + $("#search_drs_id").val() +
                  "?Q=" + $("#searchbox").val() + "&P=100&O=" + $('input[name=searchOpt]:checked').val();
                if (me2.timer) clearTimeout(me2.timer);
                me2.timer = setTimeout(function () {
                      dataAdapter.dataBind();
                }, 300);
             });

            //handler for clear searchbox form
            $("#clearsearch").on("click", function (event) {
              clearSearch();
            });
          }
       } else { //no ocr
         var $error = $('#error-modal');
         if ($error.get().length > 0) {
           $error.dialog('close');
         }
         $error = $('<div id="error-modal" style="display:none" />');
         $error.html(t['error-tmpl']({ op: "error", text: "Text search is not available for this DRS object." }));
         $error.appendTo('body');
         $error
            .dialog($.extend({title: 'Search Unavailable'}, dialogBaseOpts))
            .dialog('open');
        }
      });
    },
    "print": function(drs_id, n, slot_idx) {
      var cSlot = hMirador.viewer.workspace.slots[slot_idx];
      var cWindow = cSlot.window;
      var citLabel = cWindow.manifest.jsonLd.label;
      var img_id = ((cWindow.canvasID.split("-"))[1]).split(".json")[0];
      var content = { drs_id: drs_id, n: n, slot_idx: slot_idx, label: citLabel, img_id: img_id };
      var $dialog = $('#print-modal');

      if ($dialog.get().length > 0) {
        $dialog.dialog('close');
      }
      else {
        $dialog = $('<div id="print-modal" style="display:none" />');
        $dialog.html(t['print-tmpl'](content));
        $dialog
          .dialog($.extend({title: "Convert to PDF for Printing"}, dialogBaseOpts))
          .dialog('open');

        //set default print range max/min values
        $('#start').val('1');
        var print_slot_idx = $("#print_slot_idx").val();
        var totalSeq = hMirador.viewer.workspace.slots[print_slot_idx].window.imagesList.length;
        $('#end').val(totalSeq);

        $('input#pdssubmit').click(function(e) {
         e.preventDefault();
         printPDF(e);
        });
        $('input#pdsclear').click(function(e) {
          $('#email').val('');
          $('#start').val('1');
          $('#end').val(totalSeq);
          $('#printmsg').html('&nbsp;');
          $('input[name=printOpt]:checked').prop('checked', false);
          $('#printOptDefault').prop('checked', 'checked');
        });
      }
    },
    "links": function (drs_id, n, slot_idx) {
      var $dialog = $('#links-modal');

      if ($dialog.get().length > 0) {
        $dialog.dialog('close');
      }
      else {
        $dialog = $('<div id="links-modal" style="display:none" />');
	var json = null;
        $.getJSON( '/proxy/related/' + drs_id + '?callback=?', {'n':n})
         .done( function(json) {
            if ( (json.harvardMetadata.length > 0) || (json.relatedLinks.length > 0) ) {
		$dialog.html(t['links-tmpl']({relatedLinks: json.relatedLinks, harvardMetadata: json.harvardMetadata, op: "links", citation: json.citation}));
           	$dialog.appendTo('body');
           	$dialog
                  .dialog($.extend({title: 'Related Links'}, dialogBaseOpts))
                  .dialog('open');
            } else { //no links
                var $error = $('#error-modal');
           	if ($error.get().length > 0) {
            	   $error.dialog('close');
           	}
           	$error = $('<div id="error-modal" style="display:none" />');
           	$error.html(t['error-tmpl']({ op: "error", text: "No related links are available for this DRS object." }));
           	$error.appendTo('body');
           	$error
            	  .dialog($.extend({title: 'No Related Links available'}, dialogBaseOpts))
            	  .dialog('open');
            }
        });
      }
    },
    "viewtext": function (drs_id, n, slot_idx) {
      var $dialog = $('#viewtext-modal');

      if ($dialog.get().length > 0) {
        $dialog.dialog('close');
      }
      else {
        $dialog = $('<div id="viewtext-modal" style="display:none" />');
 	var json = null;
	$.getJSON( '/proxy/get/' + drs_id + '?callback=?', {'n':n})	
	  .done( function(json) {
	    if ( json.page.text ) {
	      $dialog.html(t['viewtext-tmpl']({op: "viewtext", text: json.page.text}));
	      $dialog.appendTo('body');
	      $dialog
		.dialog($.extend({title: 'View Text'}, dialogBaseOpts))
		.dialog('open');
	    } else {
	      $dialog.html(t['viewtext-tmpl']({ op: "viewtext", text: "No text is available for this page." }));
	      $dialog.appendTo('body')
	        .dialog($.extend({title: 'Text Unavailable'}, dialogBaseOpts))
	        .dialog('open');
	    }
        });
      }
    }


  };


  var copyCanvas = function(targetCanvas, label) {
    var miradorCanvas = targetCanvas; //document.getElementById("canvas");
    var canvasContext = miradorCanvas.getContext("2d");
    var bufferCanvas = document.getElementById("buffer");
    var bufferContext = bufferCanvas.getContext("2d");

    bufferCanvas.width = miradorCanvas.width;
    bufferCanvas.height = miradorCanvas.height;
    var oldCanvasHeight = bufferCanvas.height;
    bufferCanvas.height = bufferCanvas.height + 40;

   /* var img = new Image();
    img.crossOrigin = '';
    img.onload = function() {
        bufferContext.drawImage(img,0,0);
     };
     img.src = miradorCanvas.toDataURL();
   */

    bufferContext.drawImage(miradorCanvas, 0, 0);
    bufferContext.font="12px Helvetica";
    bufferContext.strokeText(label, 10, oldCanvasHeight + 10);

    bufferCanvas.toBlob(function(blob) {
      saveAs(blob, "download.jpg");
    }, 'image/jpg');
  };


//target .mirador-icon-save-image
//.layout-slot .slot .window .content-container .view-container .image-view .mirador-osd .openseadragon-container .openseadragon-canvas canvas
 /*$(document).on('contextmenu', 'canvas', function() { 
	console.log("contextmenu bind test successful");
  });*/
  //$('canvas').contextmenu({

  //$(document).on('contextmenu', 'canvas, .mirador-icon-save-image', function() {

  var saveImage = function(e) {
    //delegate: ".openseadragon-canvas",
    //menu: [ {title: "Save image", cmd: "save", uiIcon: "ui-icon-disk"} ],
    //select: function(event, ui) {
    //$('mirador-icon-save-image').click( function (e){ 
      e.preventDefault();
      var layout_slot = $(this).parents('.layout-slot');
      var slot_idx = layout_slot[0].attributes[1].textContent;
      var slot = null;
      if (hMirador.viewer.workspace.slots.length == 1) {
	 slot = hMirador.viewer.workspace.slots[0];
      } else {
         for (var sl = 0; sl < hMirador.viewer.workspace.slots.length; sl++) {
	   var slt = hMirador.viewer.workspace.slots[sl];
	   if (slt.slotID == slot_idx) {
             slot = hMirador.viewer.workspace.slots[sl];
             break;
	   }
         }
      }
      var mirWindow = slot.window;
      var uri = mirWindow.manifest.uri,
            parts = uri.split("/"),
            last_idx = parts.length - 1,
            drs_match = parts[last_idx].match(/drs:(\d+)/),
            drs_id = drs_match && drs_match[1],
	    img_id = ((mirWindow.currentCanvasID.split("-"))[1]).split(".json")[0],
            focusType = mirWindow.currentFocus,
	    n = mirWindow.focusModules[focusType].currentImgIndex + 1;

       if (focusType !== "ImageView") {
         var $error = $('#error-modal');
      	 if ($error.get().length > 0) {
       	    $error.dialog('close');
      	  }
      	  $error = $('<div id="error-modal" style="display:none" />');
      	  $error.html(t['error-tmpl']({ op: "error", text: "The Save Image function is only available in single page viewing mode." }));
      	  $error.appendTo('body');
      	  $error.dialog($.extend({title: 'Function Unavailable'}, dialogBaseOpts)).dialog('open');
	  return;
       }

       if (drs_id == null) return;
     /* canvas copy no longer used bc of cors/tainted canvas side effects
            var targetCanvas = this.children[0].children[4].children[1].children[2].children[1].children[7].children[0].children[0].children[1];
            targetCanvas.crossOriginPolicy = 'Anonymous';
            $.getJSON( '/proxy/getcaption/' + drs_id + '?callback=?' )
              .done(function (data) {
                 if (data.caption) {
	           label = data.caption;
                 } //TODO: Else graceful error display
	        if (ui.cmd === "save") {
	           copyCanvas(targetCanvas, label);
	        }
             });
      */
       /*var caption_url = l.PDS_VIEW_URL.replace("view","showcaption") + drs_id + '?n=' + n;
       window.open(caption_url,'');*/
       window.open(l.IDS_VIEW_URL + img_id + '?buttons=y');
      
    //}
  };


  $(document).on('click', "a.cite, a.view-in-pds, a.search, a.print, a.viewtext, a.links", present_choices);
  $(document).on('click', "a.help", display_help);
  $(document).on('contextmenu', 'canvas', saveImage);
  $(document).on('click', '.mirador-icon-save-image', saveImage);

  History.Adapter.bind(window,'statechange',function(){ // Note: We are using statechange instead of popstate
    var State = History.getState(); // Note: We are using History.getState() instead of event.state
  });

  var state_replacer = function (e, cvs_data){
    History.replaceState({}, document.title, constructUrl());
  };

  $.subscribe("windowUpdated", function (e, data){
    History.replaceState({}, document.title, constructUrl());
    $.unsubscribe("currentCanvasIDUpdated." + data.id, state_replacer);
    $.subscribe("currentCanvasIDUpdated." + data.id, state_replacer);
  });

  $.subscribe("windowAdded", function (e, data) {
    $.unsubscribe("currentCanvasIDUpdated." + data.id, state_replacer);
    $.subscribe("currentCanvasIDUpdated." + data.id, state_replacer);
  });

  $.subscribe("windowRemoved", function (e, data) {
    $.unsubscribe("currentCanvasIDUpdated." + data.id, state_replacer);
    History.replaceState({}, document.title, constructUrl(data.id));
  });

/* Download plugin code */
var DownloadButton = {
  downloadBaseUrl: "https://download.digitale-sammlungen.de/BOOKS/download.pl?",
  manifestUrlPattern: /^https?:\/\/api(?:-dev|-stg)?\.digitale-sammlungen\.de\/iiif\/presentation\/v2\/(bsb.*?)\/manifest/,
  imageUrlTemplate: hMirador.Handlebars.compile("{{imageBaseUrl}}/full/{{size}}/0/default.jpg"),
  buttonTemplate: hMirador.Handlebars.compile(['<span class="mirador-btn mirador-icon-download" role="button" title="Download">', '<i class="fa fa-download fa-lg fa-fw"></i>', '<i class="fa fa-caret-down"></i>', '<ul class="dropdown download-list">', '<li title="PDF-Download"><a href="{{downloadUrl}}" target="_blank">', '<i class="fa fa-file-pdf-o fa-lg fa-fw"></i>PDF-Download', "</a></li>", '<li title="IIIF-Manifest"><a href="{{manifestUrl}}" target="_blank">', '<i class="fa fa-file-text-o fa-lg fa-fw"></i>IIIF-Manifest', "</a></li>", "{{#each metadataUrls}}", '<li title="({{this.title}})">', '<a href="{{this.href}}" target="_blank">', '<i class="fa fa-file-text-o fa-lg fa-fw"></i>{{this.title}}', "</a></li>", "{{/each}}", "{{#each imageUrls}}", '<li class="{{#if (eq this "#")}}disabled {{/if}}image-link" title="JPG ({{this.title}})">', '<a href="{{this.href}}" target="_blank">', '<i class="fa fa-file-image-o fa-lg fa-fw"></i>JPG (<span class="dimensions">{{this.title}}</span>)', "</a></li>", "{{/each}}", "</ul>", "</span>"].join("")),
  extendDownloadUrl: function(i, t, e) {
    var a = this.downloadBaseUrl;
    return -1 === i.indexOf("_") ? a += "id=" + i : a += "id=" + i.split("_")[0] + "&ersteseite=" + t + "&letzteseite=" + e, a
  },
  extractImageUrls: function(i) {
    var t = i.imagesList[i.focusModules.ImageView.currentImgIndex],
        e = hMirador.Iiif.getImageUrl(t),
        a = t.height / t.width,
        n = [];
    return ["full", "250,"].forEach(function(l) {
      n.push({
        href: "ImageView" !== i.currentImageMode ? "#" : this.imageUrlTemplate({
          imageBaseUrl: e,
          size: l
        }),
        title: "full" === l ? t.width + "x" + t.height : parseInt(l) + "x" + Math.ceil(parseInt(l) * a)
      })
    }.bind(this)), n
  },
  extractMetadataUrls: function(i) {
    if (!Array.isArray(i)) return [];
    var t = {
      "application/marcxml+xml": "MarcXML",
      "application/rdf+xml": "RDF/XML"
    };
    return i.reduce(function(i, e) {
      return e.format && /(application\/marcxml\+xml)|(application\/rdf\+xml)/.test(e.format) && i.push({
        href: e["@id"],
        title: t[e.format]
      }), i
    }, [])
  },
  init: function() {
    hMirador.Handlebars.registerHelper("eq", function(i, t) {
      return i === t
    }), this.injectWindowEventHandler(), this.injectWorkspaceEventHandler()
  },
  injectButtonToMenu: function(i, t, e, a, n) {
    $(i).prepend(this.buttonTemplate({
      downloadUrl: t,
      imageUrls: a,
      manifestUrl: e,
      metadataUrls: n
    }))
  },
  injectWindowEventHandler: function() {
    var i = this,
        t = hMirador.Window.prototype.bindNavigation;
    hMirador.Window.prototype.bindNavigation = function() {
      t.apply(this), this.element.find(".window-manifest-navigation").on("mouseenter", ".mirador-icon-download", function() {
        this.element.find(".download-list").stop().slideFadeToggle(300)
      }.bind(this)).on("mouseleave", ".mirador-icon-download", function() {
        this.element.find(".download-list").stop().slideFadeToggle(300)
      }.bind(this))
    };
    var e = hMirador.Window.prototype.bindEvents;
    hMirador.Window.prototype.bindEvents = function() {
      e.apply(this), this.eventEmitter.subscribe("windowUpdated", function(t, e) {
        if (this.id === e.id && e.viewType) if ("ImageView" === e.viewType) {
          var a = i.extractImageUrls(this);
          this.element.find(".image-link").removeClass("disabled").attr("title", function(i) {
            return "JPG (" + a[i].title + ")"
          }).find("a").attr("href", function(i) {
            return a[i].href
          }).find("span.dimensions").text(function(i) {
            return a[i].title
          })
        } else this.element.find(".image-link").addClass("disabled")
      }.bind(this))
    }
  },
  injectWorkspaceEventHandler: function() {
    var i = this,
        t = hMirador.Workspace.prototype.bindEvents;
    hMirador.Workspace.prototype.bindEvents = function() {
      t.apply(this), this.eventEmitter.subscribe("windowAdded", function(t, e) {
        var a = this.windows.filter(function(i) {
          return i.id === e.id
        })[0],
            n = a.manifest.jsonLd["@id"],
            l = n.match(i.manifestUrlPattern);
        if (null !== l) {
          var r = l[1],
              o = a.manifest.jsonLd.sequences[0].canvases,
              s = o[0].images[0].resource["@id"].split("_").pop().split("/").shift(),
              d = o[o.length - 1].images[0].resource["@id"].split("_").pop().split("/").shift(),
              f = i.extendDownloadUrl(r, s, d),
              c = i.extractImageUrls(a),
              m = i.extractMetadataUrls(a.manifest.jsonLd.seeAlso),
              p = a.element.find(".window-manifest-navigation");
          i.injectButtonToMenu(p, f, n, c, m)
        }
      }.bind(this))
    }
  }
};
$(document).ready(function() {
  DownloadButton.init()
});



/* Share plugin code */
var ShareButtons = {
  /* all of the needed locales */
  locales: {
    'en': {
      'share-buttons-info': 'By clicking on one of the share buttons, you will leave this website.',
      'share-on-envelope': 'Share via mail',
      'share-on-facebook': 'Share on Facebook',
      'share-on-pinterest': 'Share on Pinterest',
      'share-on-tumblr': 'Share on Tumblr',
      'share-on-twitter': 'Share on Twitter',
      'share-on-whatsapp': 'Share via Whatsapp'
    }
  },

  /* options of the plugin */
  showExternalLinkInfo: false,

  /* the template for the buttons */
  buttonsTemplate: hMirador.Handlebars.compile([
    '{{#if showExternalLinkInfo}}',
    '<div id="share-buttons-info" class="alert alert-info" role="alert">{{t "share-buttons-info"}}</div>',
    '{{/if}}',
    '<div id="share-buttons" class="pull-left">',
    '{{#each shareButtons}}',
    '<a type="button" class="share-button" id="share-on-{{this}}" title="{{t (concat this)}}" target="_blank" data-target="{{this}}">',
    '<span class="fa-stack fa-lg">',
    '<i class="fa fa-circle fa-stack-2x"></i>',
    '<i class="fa fa-{{this}} fa-stack-1x" aria-hidden="true"></i>',
    '</span>',
    '</a>',
    '{{/each}}',
    '</div>'
  ].join('')),

  /* the templates for the different links */
  linkTemplates: {
    'envelope': hMirador.Handlebars.compile(
      'mailto:?subject={{{label}}}{{#if attribution}} ({{attribution}}){{/if}}&body={{{label}}}{{#if attribution}} ({{{attribution}}}){{/if}}: {{link}}'
    ),
    'facebook': hMirador.Handlebars.compile(
      'https://www.facebook.com/sharer/sharer.php?title={{{label}}} {{#if attribution}} ({{attribution}}){{/if}}&u={{link}}'
    ),
    'pinterest': hMirador.Handlebars.compile(
      'http://pinterest.com/pin/create/bookmarklet/?url={{link}}&description={{{label}}}%20{{#if attribution}}%20({{attribution}}){{/if}}&media={{{thumbnailUrl}}}'
    ),
    'tumblr': hMirador.Handlebars.compile(
      'http://www.tumblr.com/share/link?url={{link}}&name={{{label}}} {{#if attribution}} ({{attribution}}){{/if}}&tags=iiif'
    ),
    'twitter': hMirador.Handlebars.compile(
      'https://twitter.com/intent/tweet?text={{{truncate label attribution}}}&url={{link}}&hashtags=iiif'
    ),
    'whatsapp': hMirador.Handlebars.compile(
      'whatsapp://send?text={{{label}}} {{#if attribution}} ({{attribution}}){{/if}}: {{link}}'
    )
  },

  /* initializes the plugin */
  init: function(showExternalLinkInfo){
    hMirador.Handlebars.registerHelper('concat', function(target){
      return 'share-on-' + target;
    });
    hMirador.Handlebars.registerHelper('truncate', function(label, attribution){
      var text = label + (attribution ? ' (' + attribution + ')' : '');
      if(text.length > 60){
        text = text.substring(0, 60) + '...';
      }
      return text;
    });
    this.showExternalLinkInfo = showExternalLinkInfo || false;
  },

  /* injects the buttons to the target selector element */
  injectButtonsToDom: function(targetSelector, position){
    var shareButtons = ['facebook', 'twitter', 'pinterest', 'tumblr', 'envelope'];
    if('ontouchstart' in window || navigator.maxTouchPoints){
      shareButtons.push('whatsapp');
    }
    if(position === undefined || ['beforebegin', 'afterbegin', 'beforeend', 'afterend'].indexOf(position) === -1){
      position = 'afterbegin';
    }
    document.querySelector(targetSelector).insertAdjacentHTML(position, this.buttonsTemplate({
      'shareButtons': shareButtons,
      'showExternalLinkInfo': this.showExternalLinkInfo
    }));
  },

  /* updates the button links with the given parameters */
  updateButtonLinks: function(data){
    var this_ = this;
    $('#share-buttons > .share-button').attr('href', function(){
      return this_.linkTemplates[$(this).data('target')]({
        'label': data.label,
        'attribution': data.attribution,
        'link': data.link,
        'thumbnailUrl': data.thumbnailUrl
      });
    });
  }
};


});
