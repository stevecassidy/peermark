
var CSSBaseURL = "cgi-bin/marking.py?mode=css&id=";


function reloadMainFrame() {
	
   var oframe = parent.sample
   
   oframe.location = "../clt.html"
	
}

function showHelpMainFrame() {
   var oframe = parent.sample
   
   oframe.location = "../help.html"
   
}


function insertOtherFrameCSS() {

  var agt = navigator.userAgent.toLowerCase()
  // first bump if we're not inside Firefox
  if (agt.indexOf('firefox') == -1) {
    alert("These pages will only work properly with the Firefox browser.");
    return;
  }


   var odoc = parent.sample.document

   if (odoc.getElementById) {

     var headnode = odoc.getElementsByTagName("head")[0]

     // remove any existing stylesheets
     var links = headnode.getElementsByTagName("link")
     for(var i = 0; i<links.length; i++) {
       if (links[i].getAttribute("rel") == "stylesheet") {
	 headnode.removeChild(links[i])
       }
     }

     var l=odoc.createElementNS("http://www.w3.org/1999/xhtml","link");
     l.setAttribute("rel", "stylesheet");
     l.setAttribute("type", "text/css");
     l.setAttribute("href", "default.css");
     l.setAttribute("id", "thecss");
     headnode.appendChild(l);
   }
   return(false);
}

function setOtherFrameCSS(sheet) {

  var agt = navigator.userAgent.toLowerCase()
  // first bump if we're not inside Firefox
  if (agt.indexOf('firefox') == -1) {
    alert("These pages will only work properly with the Firefox browser.");
    return;
  }

  var odoc = parent.sample.document;

  if (odoc.getElementById) {
    odoc.getElementById("thecss").setAttribute("href", sheet);
  }
}


// Load a Random CSS stylesheet by querying the server for a name
function loadRandomCSS() {
	
   var sheetID = randomIdentifier();
   setOtherFrameCSS(CSSBaseURL + sheetID);
   document.vote.cssid.value = sheetID;
   
   return false;
}

function randomIdentifier()
{
  var length = 10;
  var chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890";
  var str = "";
  for(x=0;x<length;x++)
  {
    i = Math.floor(Math.random() * 62);
    str += chars.charAt(i);
  }
  return str;
}


