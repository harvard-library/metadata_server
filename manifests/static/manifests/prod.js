$(function() {
  // Localize & shorthand django vars
  var l = window.harvard_md_server;

  var dialogBaseOpts = {
    modal: true,
    draggable: false,
    resizable: false,
    width: "50%",
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
    var totalSeq = Mirador.viewer.workspace.slots[print_slot_idx].window.imagesList.length;


    var printMode = $('input[name=printOpt]:checked', '#printpds').val();
    var email = $("#email").val();
    var start = $("#start").val();
    var end = $("#end").val();
    var emailValid =  validateEmail(email);


    if (printMode === "current") {
      url = url + '?n=' + n +'&printOpt=single';
      window.open(url,'');
    } else if (printMode === "range") {
      if ((start > end) || (start === '') || (end ==='')){
        $('#printmsg').css('color', '#A51C30');
        $('#printmsg').html('<b>Invalid Sequence Range.</b>');
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


  Mirador({
    "id": "viewer",
    "layout": l.LAYOUT,
    "saveSession": false,
    "mainMenuSettings" : {
      "buttons": { 
         bookmark: false,
	fullScreenViewer: false
      },
      "userButtons": [
        {"label": "Help",
         "iconClass": "fa fa-question-circle",
         "attributes": { "class": "help", "href": "http://nrs.harvard.edu/urn-3:hul.ois:hlviewerhelp"}},
        {"label": "View in PDS",
         "iconClass": "fa fa-external-link",
         "attributes": { "class": "view-in-pds", "href": "#no-op"}},
        {"label": "Cite",
         "iconClass": "fa fa-quote-left",
         "attributes": { "class": "cite", "href": "#no-op"}},
        {"label": "Search",
         "iconClass": "fa fa-search",
         "attributes": { "class": "search", "href": "#no-op"}},
        {"label": "Print",
         "iconClass": "fa fa-print",
         "attributes": { "class": "print", "href": "#no-op"}},
        {"label": "View Text",
         "iconClass": "fa fa-font",
         "attributes": { "class": "viewtext", "href": "#no-op"}},
        {"label": "Related Links",
         "iconClass": "fa fa-link",
         "attributes": { "class": "links", "href": "#no-op"}},

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

  $('.user-buttons').slicknav({
    label: 'Menu',
    prependTo: '.mirador-main-menu-bar'
  });

  var ftype_alias = {
    'ImageView': 'i',
    'BookView': 'b',
    'ScrollView': 's',
    'ThumbnailsView': 't'
  };

  var constructUrl = function (omit_id) {
    var object_ids = $.map(Mirador.viewer.workspace.slots, function (slot, i) {
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
    var choices = $.map(Mirador.viewer.workspace.slots, function (slot, i) {
      var mirWindow = slot.window;
      var mirSlotID = slot.slotID;
      if (mirWindow) {
        var uri = mirWindow.manifest.uri,
            parts = uri.split("/"),
            last_idx = parts.length - 1,
            drs_match = parts[last_idx].match(/drs:(\d+)/),
            drs_id = drs_match && drs_match[1],
            focusType = mirWindow.currentFocus,
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
  var operations = {
    "view-in-pds": function (drs_id, n, slot_idx) {
      window.open(l.PDS_VIEW_URL + drs_id + "?n=" + n);
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
          var cSlot = Mirador.viewer.workspace.slots[slot_idx];
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
                 xhr.cache = true;
              }
            });

            //search hitlist
            $("#hitlist").jqxListBox(
             { source: dataAdapter,
              displayMember: "context",
              valueMember: "uri",
              width: 800,
              height: 200,
              renderer: function (index, label, value) {
                var record = dataAdapter.records[index];
                if (record != null) {
                    var sequence = parseInt((record.uri.split("="))[1]);
                    sequence = sequence - 1;
                    var curr_slot_idx = $("#current_slot_idx").val();
                    var currSlot = Mirador.viewer.workspace.slots[curr_slot_idx];
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
                    var currSlot = Mirador.viewer.workspace.slots[curr_slot_idx];
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
      var cSlot = Mirador.viewer.workspace.slots[slot_idx];
      var cWindow = cSlot.window;
      var citLabel = cWindow.manifest.jsonLd.label;
      var img_id = ((cWindow.currentCanvasID.split("-"))[1]).split(".json")[0];
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
        var totalSeq = Mirador.viewer.workspace.slots[print_slot_idx].window.imagesList.length;
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
        $.get( '/proxy/related/' + drs_id + '?n=' + n, function(xml){
          var json = $.xml2json(xml);
          if (json.link) {
            // Normalize to array for Handlebars
            if (!json.link.length) { json.link = [json.link]}

            $dialog.html(t['links-tmpl']({links: json.link, op: "links", citation: json.citation}));
            $dialog.appendTo('body');
            $dialog
                .dialog($.extend({title: 'Related Links'}, dialogBaseOpts))
                .dialog('open');
          }
        }); //TODO: Else graceful error display
      }
    },
    "viewtext": function (drs_id, n, slot_idx) {
      var $dialog = $('#viewtext-modal');

      if ($dialog.get().length > 0) {
        $dialog.dialog('close');
      }
      else {
        $dialog = $('<div id="viewtext-modal" style="display:none" />');
        $.get( '/proxy/get/' + drs_id + '?n=' + n, function(xml){
          var json = $.xml2json(xml);
          if (json.text) {
            $dialog.html(t['viewtext-tmpl']({op: "viewtext", text: json.text}));
            $dialog.appendTo('body');
            $dialog
                .dialog($.extend({title: 'View Text'}, dialogBaseOpts))
                .dialog('open');
          }
          else {// throw up error window
            $dialog.html(t['viewtext-tmpl']({ op: "viewtext", text: "No text is available for this page." }));
            $dialog.appendTo('body');
            $dialog
               .dialog($.extend({title: 'Text Unavailable'}, dialogBaseOpts))
               .dialog('open');
          }
        }); //TODO: Else graceful error display
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
    bufferContext.strokeText(label, 10, oldCanvasHeight + 10);

    bufferCanvas.toBlob(function(blob) {
      saveAs(blob, "download.png");
    });
  };


  $('.layout-slot').contextmenu({
    //delegate: ".openseadragon-canvas",
    menu: [ {title: "Save image", cmd: "save", uiIcon: "ui-icon-disk"} ],
    select: function(event, ui) {
      var targetCanvas = this.children[0].children[4].children[1].children[2].children[1].children[7].children[0].children[1].children[0];
      targetCanvas.crossOriginPolicy = 'Anonymous';
      /*var label = this.children[0].children[4].children[0].children[3].textContent;
        console.log("canvas label: " + label );
        console.log("select " + ui.cmd + " on " + targetCanvas.nodeName );
        if (ui.cmd === "save") {
           copyCanvas(targetCanvas, label);
        }
       */
      var label = this.children[0].children[4].children[0].children[3].textContent;
      var drs_id = "400627084"; //TEST
      $.getJSON( '/proxy/getcaption/' + drs_id + '?callback=?' )
	.fail( function() { console.log("call failed") }; )
        .success(function (data) {
          console.log("hi");
          if (data.caption) {
	    label = data.caption;
	    console.log("pds label: " + data.caption );
          } //TODO: Else graceful error display
	  if (ui.cmd === "save") {
	    console.log("canvas label: " + label );
	    copyCanvas(targetCanvas, label);
	  }
      });
    }
  });


  $(document).on('click', "a.cite, a.view-in-pds, a.search, a.print, a.viewtext, a.links", present_choices);

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



});
