// example javascript to embed a map into a question

Qualtrics.SurveyEngine.addOnload(function()
{
    /*Place your JavaScript here to run when the page loads*/

    // the <iframe-id> given here MUST match the one
    // in the question HTML, and must be unique within
    // the survey section
    var ifrm = document.getElementById('map-iframe');

    // * assign url that will be embedded in the question
    // * replace <domain> with the fully qualified domain name
    //   of the site hosting the point-it-out software.
    // * supply a site ID (a slug generated from the config name) to
    //   call out a particular map configuration.
    //   (see also mapconfig examples, and map.js)
    // * provide a project ID to differentiate this question from others.
    // * make sure the 'id' is included, to tie this response to the
    //   record stored in the web application database


    var id = "${e://Field/ResponseID}";
    ifrm.setAttribute('src', 'https://<domain>/site/<site-id>/?proj_id=<project-id>&id='+id);
});

Qualtrics.SurveyEngine.addOnReady(function()
{
    /*Place your JavaScript here to run when the page is fully displayed*/
});

Qualtrics.SurveyEngine.addOnUnload(function()
{
    /*Place your JavaScript here to run when the page is unloaded*/
});
