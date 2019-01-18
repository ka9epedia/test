var gulp = require('gulp')
var pug = require('gulp-pug');
 
gulp.task('pug', () => {
//  return gulp.src(['./pug/**/*.pug', '!./pug/**/_*.pug'])
  return gulp.src(['./app/views/*.pug', '!./pug/**/_*.pug'])
  .pipe(pug({
    pretty: true
  }))
  .pipe(gulp.dest('./html/'));
});
