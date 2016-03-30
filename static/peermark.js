
function reloadMainFrame() {
	
   var oframe = parent.sample
   
   oframe.location = "/submission/";
   oframe.location.reload(true);
}

function showHelpMainFrame() {
   var oframe = parent.sample;
   
   oframe.location = "/static/help.html";
   
}

function viewSelf() {

   form = document.getElementById("voteform");


   if (form.style.display == "none") {

       form.style.display = "block";

       document.getElementById("ownlink").innerHTML = "View Your Submission";

       parent.sample.location = "/submission/";

   } else {

       parent.sample.location = "/self/index.html";

       form.style.display = "none";

       document.getElementById("ownlink").innerHTML = "Return to Marking";
   }

}
