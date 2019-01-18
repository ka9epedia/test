exports.pgr_TSP = function(req, res) {
  var pg = require('pg');
  var config = require('../config/config');
  var async = require('async');
  var conString = "postgres://" + config.database.username + ":" + config.database.password + "@" + config.database.host + "/" + config.database.dbname;
  var client = new pg.Client(conString);
  var reqPoint = [];

  var point = [];
  var i = 0,
    j = 0;
  var queryStreets = [];

  client.connect(function(err) {
    if (err) {
      throw err;
    }
  });

  async.waterfall([
    function(callback) {
      //check req type, then use req.query or req.body
      if (req.method != 'GET') {
        eliminate(req.body.latlngs, callback);
      } else {
        eliminate(req.query.latlngs, callback);
      }
    },
    function(points, callback) {
      getPgrVertices(points, callback);
    },
    function(routes, callback) {
      getDijkstra(routes, callback);
    }
  ], function(err, result) {
    if (err) {
      console.error("Error: ", err);
    } else {
      allDone(result);
    }
  });

  // delete duplicate points.
  function eliminate(points, callback) {
    var eliPoints = [];
    if (Array.isArray(points) && points.length > 0) {
      eliPoints.push(points[0]);
      for (var i = 1; i < points.length; i++) {
        if (!(points[i].lat === points[i - 1].lat && points[i].lng === points[i - 1].lng)) {
          eliPoints.push(points[i]);
        }
      }
    }
    callback(null, eliPoints);
  }

  function getTsp(routesBeginEnd, callback) {
    var routes = [];

    // query pgrouting method 'tsp' here
    var tsp = function(tsp, callback) {

//    var qStr0 = "CREATE OR REPLACE FUNCTION pgr_eucledianTSP(" +
//                 "coordinates_sql TEXT," +
//                 "start_id BIGINT DEFAULT -1," +
//                 "end_id BIGINT DEFAULT -1," +
//                 "randomize BOOLEAN DEFAULT true," +
//                 "max_processing_time FLOAT DEFAULT '+infinity'::FLOAT," +
//                 "tries_per_temperature INTEGER DEFAULT 500," +
//                 "max_changes_per_temperature INTEGER DEFAULT 60," +
//                 "max_consecutive_non_changes INTEGER DEFAULT 200," +
//                 "initial_temperature FLOAT DEFAULT 100," +
//                 "final_temperature FLOAT DEFAULT 0.1," +
//                 "cooling_factor FLOAT DEFAULT 0.9," +
//               ");";

//      client.query(qStr0, function(err, result) {
//        if (err) {
//          console.log(qStr);
//          return console.error('✗ Postgresql Running Query Error', err);
//        }

//        var r = parsingData(result.rows);
//        var queryStreets = collectLines(r);
//        callback(null, queryStreets);
//      });
//    };

    var qStr = "SELECT * FROM pgr_TSP(" +
                 "$$" +
                   "SELECT * FROM pgr_withPointsCostMatrix(" +
                     "'SELECT id, source, target, cost, reverse_cost FROM edge_table ORDER BY id'," +
                     "'SELECT pid, edge_id, fraction from pointsOfInterest'," +
                     "array[-1, 3, 5, 6, -6], directed := false);" +
                 "$$," +
                 "start_id := 5," +
                 "randomize := false" +
               ");";

      client.query(qStr, [route.begin, route.end], function(err, result) {
        if (err) {
          console.log(qStr);
          return console.error('✗ Postgresql Running Query Error', err);
        }

        var r = parsingData(result.rows);
        var queryStreets = collectLines(r);
        callback(null, queryStreets);
      });
    };

    async.map(routesBeginEnd, dijkstra, function(err, result) {
      if (err) {
        callback(err, null);
      } else {
        callback(null, result);
      }
    });
  }

  function toGeoJson(road, type, points) {
    if (road === "") {
      road = "unknown";
    }
    var geoJson = {
      "road": road,
      "type": type,
      "coordinates": points
    };
    return geoJson;
  }

  // parsing the result from query.
  function parsingData(data) {
    // the data is like : "SRID=4326;LINESTRING(120.2121912 22.9975817,120.2123558 22.9982876)"
    var x = 0;
    var result = [];
    for (var i = 0; i != data.length; i++) {
      var points = [];
      var y = 0;
      var tmp = data[i].st_asewkt.split('(');
      var tmp2 = tmp[1].split(')');
      var tmp3 = tmp2[0].split(',');
      for (var j = 0; j != tmp3.length; j++) {
        var tmp4 = tmp3[j].split(' ');
        var point = [tmp4[0], tmp4[1]];
        points[y] = point;
        y++;
      }
      var geoObj = toGeoJson(data[i].name, "LineString", points);
      result[x++] = geoObj;
    }

    return result;
  }

  function collectLines(result) {
    var _result = [];
    var road = "";
    var lines = [];
    for (var i = 0; i < result.length; i++) {
      if (result[i].road !== road) {
        var a = {
          "road": road,
          "lines": lines
        };
        _result.push(a);
        lines = [];
      }
      road = result[i].road;
      lines.push(result[i]);
    }
    _result.push({
      "road": road,
      "lines": lines
    });

    return _result;
  }

  function allDone(data) {
    res.status(200).send(data);
  }
};
