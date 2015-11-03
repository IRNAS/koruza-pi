var path = require('path');

var rootAssetPath = './assets';

var ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');

module.exports = {
    entry: {
        dashboard: [
            rootAssetPath + '/scripts/dashboard.js',
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
                loader: 'style-loader!css-loader'
            },
            {
                test: /\.json$/,
                loader: 'json-loader'
            }
        ]
    },
    plugins: [
        new ManifestRevisionPlugin(path.join('build', 'manifest.json'), {
            rootAssetPath: rootAssetPath,
            ignorePaths: ['/styles', '/scripts']
        })
    ]
}
