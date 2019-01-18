// recommender ~json process~ 
/*
var fs = require('fs');                                                             

var json_data = fs.readFileSync("./../../tm/output-okayama.json", "utf-8");
var text = JSON.parse(json_data);

console.log(text);
text_count = 0;
for (var i in text) {
//  console.log(text[i].word);
  if(text == text) {
    text_count += 1;
  }
}
*/
//console.log(recommend_text);
/*
(function (handleload) {
  var XMLHttpRequest = require('xmlhttprequest').XMLHttpRequest;
  var xhr = new XMLHttpRequest;

  xhr.addEventListener('load', handleload, false);
  xhr.open('GET', './../../tm/output-okayama.json', 'utf-8', true);
  xhr.send(null);
}(function handleLoad (event) {
  var xhr = event.target,
      obj = JSON.parse(xhr.responseText);

  console.log(obj);
}));




  recommed: function (handleload) {
    var xhr = new XMLHttpRequest;

    xhr.addEventListener('load', handleload, false);
    xhr.open('GET', './tm/output-okayama.json', true);
    xhr.send(null);
  },
/*
    function handleLoad (event) {
    var xhr = event.target,
        obj = JSON.parse(xhr.responseText);
    console.log(obj);
    target = document.getElementById("recommend_result");
    target.innerHTML = obj;
  }
*/
