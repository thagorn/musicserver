volumeDate = new Date();
function sendMessage(/*string*/ message) {
    socket.emit("message", {data: message});
}
function toggleStations() {
    $("#stations").toggleClass("hidden");
}
function volumeChanged(/*event*/ event) {
    var slider = document.getElementById('volumeSlider');
    socket.emit("volume", {data: slider.value});
    volumeDate = new Date();
}
function setSongInfo(/* json */ data, /*bool*/ paused, /*int*/ time) {
    if(!data) {
        return;
    }
    if(!paused) {
        paused = "";
    }
    if(!time) {
        time = 0;
    }
    //Color thumbs up
    if(parseInt(data["rating"]) == 1) {
        $("#up").hide();
    } else {
        $("#up").show();
    }
    //Set timer
    console.log(data);
    musicTimer.setup(time,parseInt(data["songDuration"]));
    if(paused != "True") {
        musicTimer.Timer.play();
    }
    //Set album art
    $("#coverArt").attr("src",data["coverArt"]);
    //Set songName, artist and albumName
    $("#songName").html(data["title"]);
    $("#artist").html("<span>by: </span>" + data["artist"]);
    $("#albumName").html("<span>on: </span>" + data["album"]);
    //Set stations
    var selector = $("#stations");
    selector.html("");
    var stationList = $("<ul>");
    var curStation = data["stationName"];
    selector.append(stationList);
    var numStations = parseInt(data["stationCount"]);
    for(var i = 0; i<numStations; i++) {
        var station = "station" + i;
        var selected = "";
        if(data[station] == data["stationName"]) {
            selected = "selected='true'"
        }
        stationList.append("<li onclick='sendMessage(\"s"+i+"\\n\");'>" + data[station] + "</li>");
    }
    $("#selectedStation").html(curStation.substring(0,curStation.length-1));
}
function onPause(data) {
    if(data["paused"]) {
        $("#play").removeClass("hidden");
        $("#pause").addClass("hidden");
        musicTimer.Timer.pause();
    } else {
        $("#play").addClass("hidden");
        $("#pause").removeClass("hidden");
        musicTimer.Timer.play();
    }
}
function onVolumeChange(data) {
    if((new Date() - volumeDate) > 3000) {
        //Someone else changed the volume
        $("#volumeSlider").val(parseInt(data["volume"]));
    }
}
function initHandlers() {
    socket.on('songstart', setSongInfo);
    socket.on('songlove', function() { $("#up").hide(); });
    socket.on('onpause', onPause);
    socket.on('volumechanged', onVolumeChange);
}
var musicTimer = new (function() {
    var slider,
        incrementVal = 500, //How often to update timer in ms
        currentVal = 0,
        starVal,
        autoStart,
    updateTimer = function() {
        var val;
        currentVal += incrementVal/1000;
        slider.val(currentVal);
        val = slider.val() / (slider.attr('max') - 0);
        slider.css('background-image',
                '-webkit-gradient(linear, left top, right top, '
                + 'color-stop(' + val + ', #005050), '
                + 'color-stop(' + val + ', #006f6f)'
                + ')'
                );
    },
    init = function() {
        slider = $("#timerSlider");
        musicTimer.Timer = $.timer(updateTimer, incrementVal, false);
    };
    this.setup = function(startvalue, maxvalue) {
        currentVal = startvalue;
        slider.val(startvalue);
        slider.attr('max', maxvalue)
    };
    $(init);
});
