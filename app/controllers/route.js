exports.pgr_dijkstra = function(req, res) {

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

  function getPgrVertices(reqPoints, callback) {
    // get the nearest point of begin and end point in topology network(database).
    var getPoint = function getPoint(point, callback) {

      var qStr = "SELECT id FROM ways_vertices_pgr ORDER BY " +
        "st_distance(the_geom, st_setsrid(st_makepoint(" +
        "$1::float,$2::float), 4326)) LIMIT 1;";

      client.query(qStr, [point.lng, point.lat], function(err, result) {
        if (err) {
          callback(err, null);
        } else {
          callback(null, result.rows[0].id);
        }
      });
    };

    async.map(reqPoints, getPoint, function(err, result) {
      if (err) {
        callback(err, null);
      } else {
        var routes = [];
        // since the points array doesn't specify begin,
        // end of route, we need to divide them here.
        for (var i = 0; i < result.length - 1; i++) {
          var route = {
            "begin": result[i],
            "end": result[i + 1]
          };
          routes.push(route);
        }
        callback(null, routes);
      }
    });
  }

  function getDijkstra(routesBeginEnd, callback) {
    var routes = [];

    // query pgrouting method 'dijkstra' here
    var dijkstra = function(route, callback) {

      var qStr = "WITH result AS (SELECT * FROM ways JOIN " +
        "(SELECT seq, id1 AS node, id2 AS edge_id, cost, " +
        "ROW_NUMBER() OVER (PARTITION BY 1) AS rank FROM " +
        "pgr_dijkstra('SELECT gid::integer AS id, source::integer, " +
        "target::integer, length::double precision AS cost FROM ways'," +
        "$1, $2, false, false)) " +
        "AS route ON ways.gid = route.edge_id ORDER BY rank) " +
        "SELECT ST_AsEWKT(result.the_geom), name from result;";

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
