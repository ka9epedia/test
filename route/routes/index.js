var express   = require('express');
var Route     = express.Router();
var config    = require('../config/config');

var routeController = require(config.root + '/app/controllers/route');
//var routeController = require(config.root + '/app/controllers/tsp');

Route.get('/', function (req, res) {
  res.render('route');
  //res.render('tsp');
});

// api routes
Route.all('/routing', routeController.pgr_dijkstra);
//Route.all('/routing', routeController.pgr_TSP);
module.exports = Route;
