// Routine for 'click'
map.on('click', mapClick);

function mapClick(e) {
    var wp = osrm.getWaypoints().filter(function(pnt) {
        return pnt.latLng;
    });
    switch(wp.length) {
    case 0:
        osrm.spliceWaypoints(0, 1, e.latlng);
        break;
    case 1:
        osrm.spliceWaypoints(1, 1, e.latlng);
        break;
    default:
        osrm.spliceWaypoints(osrm.getWaypoints().length, 0, e.latlng);
        break
    }
}
