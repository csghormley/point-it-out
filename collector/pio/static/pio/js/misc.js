
$.urlParam = function(name){
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results==null || results[1]=='') {
       return null;
    }
    else {
       return decodeURI(results[1]);
    }
}

// round to the specified number of digits
// behave like Math.round if nothing specified
function round_x(num,digits=0) {
   return (Math.round(num*Math.pow(10,digits)))/Math.pow(10,digits)
}

// for user behavior
const ub_config = {
	userInfo: false,
	clicks: true,
	mouseMovement: true,
	mouseMovementInterval: 1,
	mouseScroll: false,
	timeCount: true,
	clearAfterProcess: true,
	processTime: 10,
	processData: function(results){

		if (responseid==null) {return}
		csrftoken = Cookies.get('csrftoken');

		let data = {responseid: responseid, logdata: JSON.stringify(results)};

		$.ajax({
		  type: 'POST',
		  url: '/api/visitorlog/',
		  headers: {"X-Csrftoken": csrftoken},
		  data: JSON.stringify(data),
		  contentType: "application/json",
		  dataType: 'json', // type of data expected from the server
		  success: function (responseData, textStatus, jqXHR) {
			 //console.log(JSON.stringify(responseData));
		  },
		  error: function (responseData, textStatus, errorThrown) {
			 console.log("Problem saving the log data: " + results);
		  }
		  });
	}
}

userBehaviour.config(ub_config);
userBehaviour.start();

const showHelp = $.urlParam('showHelp');
const showTutorial = parseInt($.urlParam('showTutorial'));
const showInfo = $.urlParam('showInfo');

if (showHelp == 1){
	$('#howtoModal').modal('show');
};

if (showTutorial == 1){
	$('#tutorialContent').slideDown();
}

if (showInfo == 1){
  $('#showInfo').css('display','inline');
}
