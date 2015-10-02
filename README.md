Installation
------------

First, prepare an installation package from this repository by running:

```
$ ./make-package.sh
```

This will give you a file `koruza-package.tar.bz2`, which you should copy
to the Raspberry Pi running KORUZA. You can do this by using `scp`. After
the file has been copied, connect to the Raspberry Pi and execute the
following commands:

```
$ sudo tar -xf koruza-package.tar.bz2 -C /
$ sudo /koruza/install
```

And this should install and configure all the needed services.

