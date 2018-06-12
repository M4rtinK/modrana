//.pragma library


var foo = "bar"

function formatDistance(d, scale) {
    d = d/scale
    if (! d) {
        return "0"
    }

    //TODO: imperial unit handling
    if (1) {
        if (d >= 1000) {
            return Math.round(d / 1000.0) + " " + qsTr("km")
        } else if (d >= 100) {
            return Math.round(d) + " " + qsTr("m")
        } else {
            return d.toFixed(1) + " " + qsTr("m")
        }
    }
}

function ms2kmh(ms){
    // convert meters per second to kilometers per hour
    return (ms * 3600) / 1000.0
}

function formatSpeedKmh(speedKmh) {
    // format kmh speed with l10n support
    return speedKmh + " " + qsTr("km/h")
}

function formatBearing(b) {
    return Math.round(b) + "°"
}

function formatCoordinate(lat, lon, c) {
    return getLat(lat, c) + " " + getLon(lon, c)
}

function getDM(l) {
    var out = Array(3);
    out[0] = (l > 0) ? 1 : -1
    l = out[0] * l
    out[1] = ("00" + Math.floor(l)).substr(-3, 3)
    out[2] = ("00" + ((l - Math.floor(l)) * 60).toFixed(3)).substr(-6, 6)
    return out
}

function getValueFromDM(sign, deg, min) {
    return sign*(deg + (min/60))
}

function getLat(lat, settings) {
    var l = Math.abs(lat)
    var c = "S";
    if (lat > 0) {
        c = "N"
    }
    if (settings.coordinateFormat == "D") {
        return c + " " + l.toFixed(5) + "°"
    } else {
        return c + " " + Math.floor(l) + "° " + ((l - Math.floor(l)) * 60).toFixed(3) + "'"
    }
}

function getLon(lon, settings) {
    var l = Math.abs(lon)
    var c = "W";
    if (lon > 0) {
        c = "E"
    }
    if (settings.coordinateFormat == "D") {
        return c + " " + l.toFixed(5) + "°"
    } else {
        return c + " " + Math.floor(l) + "° " + ((l - Math.floor(l)) * 60).toFixed(3) + "'"
    }
}

function getMapTile(url, x, y, zoom) {
    return url.replace("%(x)d", x).replace("%(y)d", y).replace("%(zoom)d", zoom);
}

function getBearingTo(lat, lon, tlat, tlon) {
    var lat1 = lat * (Math.PI/180.0);
    var lat2 = tlat * (Math.PI/180.0);

    var dlon = (tlon - lon) * (Math.PI/180.0);
    var y = Math.sin(dlon) * Math.cos(lat2);
    var x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dlon);
    return (360 + (Math.atan2(y, x)) * (180.0/Math.PI)) % 360;
}

function getDistanceTo(lat, lon, tlat, tlon) {
    var dlat = Math.pow(Math.sin((tlat-lat) * (Math.PI/180.0) / 2), 2)
    var dlon = Math.pow(Math.sin((tlon-lon) * (Math.PI/180.0) / 2), 2)
    var a = dlat + Math.cos(lat * (Math.PI/180.0)) * Math.cos(tlat * (Math.PI/180.0)) * dlon;
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return 6371000.0 * c;
}

function p2pDistance(point1, point2) {
   var lat1 = point1.latitude
   var lon1 = point1.longitude
   var lat2 = point2.latitude
   var lon2 = point2.longitude
   return getDistanceTo(lat1, lon1, lat2, lon2)
}

function p2pDistanceString(point1, point2) {
   var lat1 = point1.latitude
   var lon1 = point1.longitude
   var lat2 = point2.latitude
   var lon2 = point2.longitude
   return formatDistance(getDistanceTo(lat1, lon1, lat2, lon2), 1)
}

String.prototype.trunc =
     function(n,useWordBoundary){
         var toLong = this.length>n,
             s_ = toLong ? this.substr(0,n-1) : this;
         s_ = useWordBoundary && toLong ? s_.substr(0,s_.lastIndexOf(' ')) : s_;
         return  toLong ? s_ +'...' : s_;
      };
