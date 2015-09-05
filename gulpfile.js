var gulp = require('gulp'),
	minifycss = require('gulp-minify-css'),
	jshint = require('gulp-jshint'),
	uglify = require('gulp-uglify'),
	imagemin = require('gulp-imagemin'),
	clean = require('gulp-clean'),
	autoprefixer = require('gulp-autoprefixer'),
	notify = require('gulp-notify'),
	concat = require('gulp-concat'),
	cache = require('gulp-cache'),
	compass = require('gulp-compass'),
	rename = require('gulp-rename'),
	htmlmin = require('gulp-htmlmin'),
	mainBowerFiles = require('main-bower-files'),
	gulpFilter = require('gulp-filter'),
	livereload = require('gulp-livereload');
	pngquant = require('imagemin-pngquant');


gulp.task('copy', function(){
    gulp.src('src/template/feed/*.xml')
				.pipe(gulp.dest('tpl/feed'))
    gulp.src('src/template/mail/*.txt')
				.pipe(gulp.dest('tpl/mail'))
});

gulp.task('image', function(){
	return gulp.src('src/img/**/**')
		.pipe(imagemin({
			progressive: true,
			svgoPlugins: [{removeViewBox: false}],
			use: [pngquant()]
		}))
		.pipe(gulp.dest('static/img'))
});

gulp.task('html', function(){
	return gulp.src('src/template/**/*.html')
        .pipe(htmlmin({collapseWhitespace: true}))
		.pipe(gulp.dest('tpl'))
});

gulp.task('css', function(){
	gulp.src('src/css/**/*.css')
		.pipe(gulp.dest('static/css'))
        .pipe(livereload())

	gulp.src('src/template/**/*.css')
		.pipe(gulp.dest('tpl'))
        .pipe(livereload())
});

gulp.task('style', function(){
	return gulp.src('src/scss/*.scss')
		.pipe(compass({
			css: 'static/css',
			sass: 'src/scss',
			sourcemap: true,
			style: 'compact',
			comments: false
		}))
		.pipe(autoprefixer('last 2 version', 'safari 5', 'ie 8', 'ie 9', 'opera 12.1', 'ios 6', 'android 4'))
		.pipe(gulp.dest('static/css'))
		.pipe(rename({suffix: '.min'}))
		.pipe(minifycss())
		.pipe(gulp.dest('static/css'))
		.pipe(notify({message: 'Style Task Complete'}));
});


gulp.task('script', function(){
	return gulp.src('src/js/*.js')
		.pipe(jshint('.jshintrc'))
		.pipe(jshint.reporter('default'))
		//.pipe(concat('main.js'))
		.pipe(gulp.dest('static/js'))
		.pipe(rename({suffix: '.min'}))
		.pipe(uglify())
		.pipe(gulp.dest('static/js'))
		.pipe(notify({message: 'Script Task Complete'}));
});

gulp.task('clean', function(){
	return gulp.src(['static', 'tpl'], {read:false})
		.pipe(clean());
});


gulp.task('bower', function(){

	var jsFilter = gulpFilter(['**/**/*.js', '**/**/*.min.js']);
   	var cssFilter = gulpFilter(['**/**/*.css', '**/**/*.min.css']);

	return gulp.src(mainBowerFiles())
		.pipe(jsFilter)
		.pipe(gulp.dest('assets/js'))
		.pipe(jsFilter.restore())
		.pipe(cssFilter)
		.pipe(gulp.dest('assets/css'))
});

gulp.task('serve', ['html', 'image', 'css', 'style', 'copy', 'script'], function(){
    livereload.listen();
	gulp.watch('src/scss/*.scss', ['style']);
	gulp.watch('src/js/*.js', ['script']);
	gulp.watch('src/template/**/*.html', ['html']);
	gulp.watch('src/img/**', ['image']);
	gulp.watch('src/css/**', ['css']);
});


gulp.task('default', ['clean'], function(){
	
});
