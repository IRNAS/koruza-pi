var path = require('path');

var rootAssetPath = './assets';

var ExtractTextPlugin = require('extract-text-webpack-plugin');
var ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');

module.exports = {
    entry: {
        dashboard: [
            rootAssetPath + '/scripts/dashboard.js'
        ],
        styles: [
            rootAssetPath + '/styles/style.css'
        ]
    },
    output: {
        path: './build/public',
        publicPath: '/public/',
        filename: '[name].[chunkhash].js',
        chunkFilename: '[id].[chunkhash].js'
    },
    resolve: {
        extensions: ['', '.js', '.jsx']
    },
    module: {
        loaders: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: 'babel-loader'
            },
            {
                test: /\.css$/,
                loader: ExtractTextPlugin.extract('style-loader', 'css-loader')
            },
        ]
    },
    plugins: [
        new ExtractTextPlugin('[name].[chunkhash].css'),
        new ManifestRevisionPlugin(path.join('build', 'manifest.json'), {
            rootAssetPath: rootAssetPath,
            ignorePaths: ['/styles', '/scripts']
        })
    ]
}
