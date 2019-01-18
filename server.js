var express   = require('express');
var path      = require('path');
var config    = require(__dirname + '/app/config/config');
var app       = express();
var PythonShell = require('python-shell');
var https = require('https');
var fs = require('fs');

app.config = config;
require('./app/config/express')(app, express);

app.listen(app.get('port'), function () {
    console.log("\n✔ Express server listening on port %d in %s mode",
        app.get('port'), app.get('env'));
});
/* test1(child_process) 

app.get('./tm/tw4',call_tw3);
function call_tw3(req, res) {
  var spawn = require('child_process').spawn;
  var process = spawn('python', ['./tm/tw4.py'
      req.query.matched_list_decision
  ]);

  process.stdout.on('data', function (data) {
      res.send(data.toString());
      });
}
*/

/* test2(npm_python_shell) */
app.get('./recommends', call_tw4);

function call_tw4(req, res) {
  var options = {
    args:
    [
      req.query.matched_list_decision,
      req.query.word
    ]
  }

  PythonShell.run('./tm/tw4.py', options, function(err, data) {
    if (err) res.send(err);
    res.send(data.toString())
  });
}

/* jsondata process
const Jsondata = "http://localhost:5050/tm/output-okayama.json";

https.get(Jsondata, function (res) {
    var body = '';
    res.setEncoding('utf8');
    res.on('data', function (chunk) {
        body += chunk;
    });
    res.on('data', function (chunk) {
        // body の値を json としてパースしている
        res = JSON.parse(body);
        console.log('${res.word}');
    })
  }).on('error', function (e) {
    console.log(e.message);
});
*/
module.exports = app;
