var DownloadButton = {
  downloadBaseUrl: "https://download.digitale-sammlungen.de/BOOKS/download.pl?",
  manifestUrlPattern: /^https?:\/\/api(?:-dev|-stg)?\.digitale-sammlungen\.de\/iiif\/presentation\/v2\/(bsb.*?)\/manifest/,
  imageUrlTemplate: Mirador.Handlebars.compile("{{imageBaseUrl}}/full/{{size}}/0/default.jpg"),
  buttonTemplate: Mirador.Handlebars.compile(['<span class="mirador-btn mirador-icon-download" role="button" title="Download">', '<i class="fa fa-download fa-lg fa-fw"></i>', '<i class="fa fa-caret-down"></i>', '<ul class="dropdown download-list">', '<li title="PDF-Download"><a href="{{downloadUrl}}" target="_blank">', '<i class="fa fa-file-pdf-o fa-lg fa-fw"></i>PDF-Download', "</a></li>", '<li title="IIIF-Manifest"><a href="{{manifestUrl}}" target="_blank">', '<i class="fa fa-file-text-o fa-lg fa-fw"></i>IIIF-Manifest', "</a></li>", "{{#each metadataUrls}}", '<li title="({{this.title}})">', '<a href="{{this.href}}" target="_blank">', '<i class="fa fa-file-text-o fa-lg fa-fw"></i>{{this.title}}', "</a></li>", "{{/each}}", "{{#each imageUrls}}", '<li class="{{#if (eq this "#")}}disabled {{/if}}image-link" title="JPG ({{this.title}})">', '<a href="{{this.href}}" target="_blank">', '<i class="fa fa-file-image-o fa-lg fa-fw"></i>JPG (<span class="dimensions">{{this.title}}</span>)', "</a></li>", "{{/each}}", "</ul>", "</span>"].join("")),
  extendDownloadUrl: function(i, t, e) {
    var a = this.downloadBaseUrl;
    return -1 === i.indexOf("_") ? a += "id=" + i : a += "id=" + i.split("_")[0] + "&ersteseite=" + t + "&letzteseite=" + e, a
  },
  extractImageUrls: function(i) {
    var t = i.imagesList[i.focusModules.ImageView.currentImgIndex],
        e = Mirador.Iiif.getImageUrl(t),
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
    Mirador.Handlebars.registerHelper("eq", function(i, t) {
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
        t = Mirador.Window.prototype.bindNavigation;
    Mirador.Window.prototype.bindNavigation = function() {
      t.apply(this), this.element.find(".window-manifest-navigation").on("mouseenter", ".mirador-icon-download", function() {
        this.element.find(".download-list").stop().slideFadeToggle(300)
      }.bind(this)).on("mouseleave", ".mirador-icon-download", function() {
        this.element.find(".download-list").stop().slideFadeToggle(300)
      }.bind(this))
    };
    var e = Mirador.Window.prototype.bindEvents;
    Mirador.Window.prototype.bindEvents = function() {
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
        t = Mirador.Workspace.prototype.bindEvents;
    Mirador.Workspace.prototype.bindEvents = function() {
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
/* $(document).ready(function() {
  DownloadButton.init()
});*/
