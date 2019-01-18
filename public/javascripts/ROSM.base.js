// ROSM base class

var ROSM = {};
ROSM.GLOBALS = {};
ROSM.CONSTANTS = {};
ROSM.DEFAULTS = {};
ROSM.C = ROSM.CONSTANTS;
ROSM.G = ROSM.GLOBALS;

ROSM.CONSTANTS.SOURCE_LABEL = "出発地";
ROSM.CONSTANTS.TARGET_LABEL = "目的地";
ROSM.CONSTANTS.VIA_LABEL = "案内";

ROSM.DEFAULTS.ZOOM_LEVEL = 14;
ROSM.DEFAULTS.HOST_GEOCODER_URL = "http://nominatim.openstreetmap.org/search";
//ROSM.DEFAULTS.HOST_GEOCODER_URL = "http://maps.googleapis.com/maps/api/geocode/";