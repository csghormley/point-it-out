/**
 * @author Taha Al-Jody <taha@ta3design.com>
 * https://github.com/TA3/web-user-behaviour
 */
var userBehaviour = (function () {
    var defaults = {
        clicks: true,
        mouseMovement: true,
        mouseMovementInterval: 1,
        mouseScroll: true,
        mousePageChange: true, //todo
        timeCount: true,
        clearAfterProcess: true, // todo
        processTime: 15,
        processData: function (results) {
            console.log(results);
        },
    };
    var user_config = {};
    var mem = {
        processInterval: null,
        mouseInterval: null,
        mousePosition: [], //x,y,timestamp
        eventListeners: {
            scroll: null,
            click: null,
            mouseMovement: null,
        },
        eventsFunctions: {
            scroll: () => {
                results.mouseScroll.push([window.scrollX, window.scrollY, getTimeStamp()]);
            },
            click: (e) => {
                results.clicks.clickCount++;
                var path = [];
                var node = "";
                e.composedPath().forEach((el, i) => {
                    if ((i !== e.composedPath().length - 1) && (i !== e.composedPath().length - 2)) {
                        node = el.localName;
                        (el.className !== "") ? el.classList.forEach((clE) => {
                            node += "." + clE
                        }): 0;
                        (el.id !== "") ? node += "#" + el.id: 0;
                        path.push(node);
                    }
                })
                path = path.reverse().join(">");
                results.clicks.clickDetails.push([e.clientX, e.clientY, path, getTimeStamp()]);
            },
            mouseMovement: (e) => {
                mem.mousePosition = [e.clientX, e.clientY, getTimeStamp()];
            }
        },
        // special for map
        mapCenter_proj: null,
        mapCenter: null,
        resolution: null
    };
    let results = {};

    function resetResults() {
        results = {
            time: { //todo
                startTime: 0,
                currentTime: 0,
            },
            clicks: {
                clickCount: 0,
                clickDetails: []
            },
            mouseMovements: [],
            mouseScroll: [],

            // special for map: a mapFrame contains a center, resolution, and array of mouseMovements
            mapFrames: []
        }
    };
    resetResults();

    function getTimeStamp() {
        return Date.now();
    };

    function saveMapFrame() {
        // record center of current view as lon/lat; keep native representation for change detection
        mem.mapCenter_proj = map.getView().getCenter();
        mem.mapCenter = ol.proj.transform(mem.mapCenter_proj, map.getView().getProjection(), 'EPSG:4326');
        mem.resolution = map.getView().getResolution();
    }

    function pushMapFrame() {
        results.mapFrames.push({startTime: getTimeStamp(), center: mem.mapCenter, resolution: mem.resolution, mouseMovements: []});
    }

    function config(ob) {
        user_config = {};
        Object.keys(defaults).forEach((i) => {
            i in ob ? user_config[i] = ob[i] : user_config[i] = defaults[i];
        })
    };

    function start() {

        if (Object.keys(user_config).length !== Object.keys(defaults).length) {
            console.log("no config provided. using default..");
            user_config = defaults;
        }
        // TIME SET
        if (user_config.timeCount !== undefined && user_config.timeCount) {
            results.time.startTime = getTimeStamp();
        }
        // MOUSE MOVEMENTS
        if (user_config.mouseMovement) {
            mem.eventListeners.mouseMovement = window.addEventListener("mousemove", mem.eventsFunctions.mouseMovement);
            mem.mouseInterval = setInterval(() => {

                // special for map: log any time the map center or resolution change
                // record mouse movements within that context
                if (map != undefined && ((mem.mapCenter_proj != map.getView().getCenter())
                                         || (mem.resolution != map.getView().getResolution()) )) {

                    // record center of current view as lon/lat; keep native representation for change detection
                    saveMapFrame();

                    pushMapFrame();
                }

                if (mem.mousePosition && mem.mousePosition.length) { //if data has been captured
                    if (!results.mouseMovements.length || ((mem.mousePosition[0] !== results.mouseMovements[results.mouseMovements.length - 1][0]) && (mem.mousePosition[1] !== results.mouseMovements[results.mouseMovements.length - 1][1]))) {
                        results.mouseMovements.push(mem.mousePosition);

                        // also log the mouse movement to the latest mapFrame object
                        if (results.mapFrames.length>0) {
                            results.mapFrames[results.mapFrames.length-1].mouseMovements.push(mem.mousePosition);
                        }
                    }
                }

            }, defaults.mouseMovementInterval * 1000);
        }
        //CLICKS
        if (user_config.clicks) {
            mem.eventListeners.click = window.addEventListener("click", mem.eventsFunctions.click);
        }
        //SCROLL
        if (user_config.mouseScroll) {
            mem.eventListeners.scroll = window.addEventListener("scroll", mem.eventsFunctions.scroll);
        }
        //PROCESS INTERVAL
        if (user_config.processTime !== false) {
            mem.processInterval = setInterval(() => {
                if (dataReady()) {
                    user_config.processData(result());
                    if (user_config.clearAfterProcess) {
                        resetResults();
                    }
                }
            }, user_config.processTime * 1000)
        }
    };

    function dataReady() {
        // wait for at least one click or two mouse movements
        if (results.mouseMovements.length>1 || results.clicks>0) return true;
    }

    function processResults() {
        user_config.processData(result());
        if (user_config.clearAfterProcess) {
            resetResults();
        }
    }

    function stop() {
        if (user_config.processTime !== false) {
            clearInterval(mem.processInterval);
        }
        clearInterval(mem.mouseInterval);
        window.removeEventListener("scroll", mem.eventsFunctions.scroll);
        window.removeEventListener("click", mem.eventsFunctions.click);
        window.removeEventListener("mousemove", mem.eventsFunctions.mouseMovement);
    }

    function result() {
        if (user_config.timeCount !== undefined && user_config.timeCount) {
            results.time.currentTime = getTimeStamp();
        }
        return results
    };

    function showConfig() {
        if (Object.keys(user_config).length !== Object.keys(defaults).length) {
            return defaults;
        } else {
            return user_config;
        }
    };
    return {
        showConfig: showConfig,
        config: config,
        start: start,
        stop: stop,
        showResult: result,
        processResults: processResults,
    };

})();
