
wget http://download.osgeo.org/gdal/2.2.0/gdal-2.2.0.tar.gz
tar -xvzf gdal-2.2.0.tar.gz
cd gdal-2.2.0/
./configure
make
make install

ldconfig

ln -s /usr/lib/libproj.so.0 /usr/lib/libproj.so
