#!/bin/bash -e

cd package
tar cvfj ../koruza-package.tar.bz2 \
	--exclude='.git*' \
	--exclude='node_modules' \
	--exclude='koruza/webui/assets' \
	--exclude='koruza/webui/webpack.config.js' \
	--exclude='koruza/webui/package.json' \
	*
cd ..

