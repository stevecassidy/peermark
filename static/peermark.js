


function showHelpMainFrame() {
   var iframe = document.getElementById('sample');
   
   iframe.location = "/help.html";
   
}

function viewSelf() {

   var form = document.getElementById("voteform");
   var iframe = document.getElementById('sample');

   if (form.style.display == "none") {

       form.style.display = "flex";

       document.getElementById("ownlink").innerHTML = "View Your Submission";

       iframe.src = "/submission/";

   } else {

       /* add a timestamp to the url to avoid cache hits */
       iframe.src = "/self/index.html?r=" + (new Date()).getTime();

       form.style.display = "none";

       document.getElementById("ownlink").innerHTML = "Return to Marking";
   }

}
