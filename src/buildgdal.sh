
# download gdal
wget http://download.osgeo.org/gdal/2.2.0/gdal-2.2.0.tar.gz
tar -xvzf gdal-2.2.0.tar.gz

# configure / compile / install
cd gdal-2.2.0/
./configure
make
make install

# reload modules
ldconfig

# rename..
ln -s /usr/lib/libproj.so.0 /usr/lib/libproj.so

# clear gdal build folder. (1gb)
rm -rf .
