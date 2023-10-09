// const webpack = require('webpack');
// const _ = require('lodash');
const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const LiveReloadPlugin = require('webpack-livereload-plugin');

// reference: https://dev.to/pascalw/django-webpack-without-any-plugins-94p


module.exports = (env, argv) => {

    // simple webpack mode.
    // use dev folder for development NOMORE
    // dist for production (under version control) NOMORE!
    // all files go to bundle directory.
    // fab deploy will create production builds an upload those.

    const base_path = './apps/djangocms4test/';
    const entry_base_path = base_path + 'static_src/';
    const out_base_path = base_path + 'static/djangocms4test/';

    let config = {
        // context: __dirname,
        name: 'main',
        plugins: [
            new MiniCssExtractPlugin(),
            new LiveReloadPlugin(),
        ],
        entry: {
            'bundle': entry_base_path + 'js/index.js',
            // 'print': entry_base_path + 'js/index_print.js',
        },
        output: {
            path: path.resolve(out_base_path + 'bundle/'),
            filename: "[name].js",
            chunkFilename: "[id]-[chunkhash].js",  // ?!
            clean: true,
        },
        module: {
            rules: [
                {
                    // the direct css job
                    test: /\.css$/i,
                    use: [
                        // Creates `style` nodes from JS strings
                        // "style-loader",
                        // creates files!
                        MiniCssExtractPlugin.loader, // Translates CSS into CommonJS
                        "css-loader",
                    ],
                },
                {
                    // the sass job
                    test: /\.s[ac]ss$/i,
                    use: [
                        // Creates `style` nodes from JS strings
                        // "style-loader",
                        // creates files!
                        MiniCssExtractPlugin.loader,
                        // Translates CSS into CommonJS
                        "css-loader",
                        // Compiles Sass to CSS
                        "sass-loader",
                    ],
                },
                {
                    test: /\.(eot|woff|woff2|ttf|png|svg|jpg|jpeg|gif)$/i,
                    type: "asset/resource",
                    generator : {
                      filename : 'assets/[name][ext][query]',
                    }
                },
                {
                    // enhancing back to IE11, maybe
                    test: /\.m?js$/,
                    exclude: /(node_modules|bower_components)/,
                    use: {
                        loader: 'babel-loader',
                        options: {
                            presets: ['@babel/preset-env'],
                            // plugins: ['@babel/plugin-proposal-object-rest-spread']
                        }
                    }
                }
            ],
        },
        // devServer: {
        //     port: 8080,
        //     writeToDisk: true, // Write files to disk in dev mode, so Django can serve the assets
        //     hot: true,  // hot module reloading...irk?
        // },
    };
    // development? different directory!
    if (argv.mode === 'development') {
        config.devtool = 'source-map';
        // config.output.path = path.resolve(out_base_path + 'dev/');
    }

    // let print_config = {};
    // _.defaultsDeep(print_config, config);
    // print_config.name = 'print';
    // print_config.entry = entry_base_path + 'sass/print.sass';
    // print_config.output.filename = 'print.js';
    // print_config.devServer.port = 8081;
    // console.log(config.name);
    // console.log(print_config.name);
    return [config];

};
