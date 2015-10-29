Development
-----------

The server backend requires the same Python dependencies as the overall KORUZA
controller package, which can be found in the top-level `requirements.txt` file.

The frontend uses NPM and Webpack to manage dependencies. Note that you need to
install these only for development as the runtime does not require neither. To
install, use the following commands in the `webui` directory:

```
$ npm install
```

After the dependencies are installed, you may rebuild the frontend assets by
running:

```
$ npm run build
```

To start the application, simply use:

```
$ python app.py
```
