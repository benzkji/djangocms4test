var gulp = require('gulp'),
    sass = require('gulp-sass'),
    consolidate = require('gulp-consolidate'),
    autoprefixer = require('gulp-autoprefixer'),
    shell = require('gulp-shell'),
    jshint = require('gulp-jshint'),
    livereload = require('gulp-livereload'),

    // iconfont = require('gulp-iconfont'),

    // svgstore = require('gulp-svgstore'),
    // svgmin = require('gulp-svgmin'),
    // path = require('path'),

    dummy = 'last';

// fix Promise() error from whiche package again?
// from the earlier days! require('es6-promise').polyfill();
var static_path = 'apps/djangocms4test/static/djangocms4test/';


// gulp.task('sass', ['iconfont', 'svgstore'], function () {
gulp.task('sass', function () {
    return gulp.src(static_path + 'sass/screen.sass')
        .pipe(sass({
            sourceComments: 'map',
            sourceMap: 'sass',
            outputStyle: 'nested'
        }).on('error', sass.logError))
        .pipe(autoprefixer("last 2 versions"))
        .pipe(gulp.dest(static_path + 'css/'))
});


// last used: losinger
gulp.task('svgstore', function () {
    return gulp
        .src(static_path + 'svgstore/*.svg')
        .pipe(cheerio({
            run: function ($) {
                //console.log($.xml());
                $('[fill]').removeAttr('fill');
                $('[style]').removeAttr('style');
            },
            parserOptions: {xmlMode: true}
        }))
        .pipe(svgmin(function (file) {
            var prefix = path.basename(file.relative, path.extname(file.relative));
            return {
                plugins: [{
                    cleanupIDs: {
                        prefix: prefix + '-',
                        minify: true
                    }
                }]
            }
        }))
        .pipe(svgstore({'inlineSvg': true}))
        .pipe(gulp.dest(static_path + '../../templates/djangocms4test/svgstore/'));
});


// last used: bos
gulp.task('iconfont', function () {
    var runTimestamp = Math.round(Date.now() / 1000);
    return gulp.src([static_path + 'iconfont/svg/*.svg'])
        .pipe(iconfont({
                fontName: 'icons', // required
                normalize: true, // recommended option
                appendUnicode: false,
                fontHeight: 1000,
                formats: ['ttf', 'eot', 'woff'], // default, 'woff2' and 'svg' are available
                timestamp: runTimestamp // recommended to get consistent builds when watching files
            }
            )
        ).on('glyphs', function (glyphs, options) {
            // CSS templating, e.g.
            console.log(glyphs, options);
            gulp.src(static_path + 'iconfont/scss/_iconfont.scss')
                .pipe(consolidate('lodash', {
                        glyphs: glyphs,
                        fontName: 'icons',
                        fontPath: '../iconfont/font/',
                        className: 'icon'
                    })
                )
                .pipe(gulp.dest(static_path + 'sass/'));
        })
        .pipe(gulp.dest(static_path + 'iconfont/font/'));
});


gulp.task('jshint', function () {
    return gulp.src(['gulpfile.js', static_path + 'js/**.js'])
        .pipe(jshint())
        .pipe(livereload());
});


gulp.task('flake8', shell.task(
    ['flake8 --ignore=errors']
    )
);


gulp.task('pip-compile', shell.task(
        [
            'pip install -U pip setuptools pip-tools',
            'pip-compile requirements/dev.in',
            // 'pip install -r requirements/dev.txt',
            'pip-sync requirements/dev.txt',
            'pip-compile requirements/deploy.in',
            'safety check',
        ]
    )
);


gulp.task('pip-compile-upgrade', shell.task(
        [
            'pip install -U pip setuptools pip-tools',
            'pip-compile requirements/dev.in --upgrade',
            // 'pip install -r requirements/dev.txt',
            'pip-sync requirements/dev.txt',
            'pip-compile requirements/deploy.in --upgrade',
            'safety check',
        ]
    )
);


gulp.task('node2static', function () {
    // jquery/ui: (and other?!)
    // save some repository space, by adding specific sub folders only
    // base is always node_modules, so a folder jquery/dist will be made
    return gulp.src(
        [
            'node_modules/jquery/dist/*',
            'node_modules/jquery-ui/ui/widget.js',
            'node_modules/slick-carousel/**/*',
            'node_modules/normalize-css/**/*',  // size ok
            'node_modules/magnific-popup/**/*',
        ],
        {'base': 'node_modules',}
    )
        .pipe(gulp.dest(static_path + '/libs/'));
});


gulp.task('default', gulp.parallel('sass', 'node2static', 'pip-compile', 'jshint', 'flake8'));


gulp.task('watch', function () {
    livereload.listen();
    gulp.watch([
        'apps/**/*.html',
        'apps/**/*.py',
        static_path + 'css/*',
        static_path + 'js/*',
    ]).on('change', livereload.changed);
    gulp.watch(static_path + 'sass/*.sass', gulp.series('sass'));
    // gulp.watch(static_path + 'iconfont/svg/*.svg', ['iconfont']);
    // gulp.watch(static_path + 'svgstore/*.svg', ['svgstore']);
    gulp.watch('requirements/*.in', gulp.series('pip-compile'));
    gulp.watch(['gulpfile.js', static_path + 'js/**.js'], gulp.series('jshint'));
    gulp.watch('apps/**/*.py', gulp.series('flake8'));
});
