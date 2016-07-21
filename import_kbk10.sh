#!/usr/bin/env bash

rootdir=/app/kbk/kbk10
tempdir=/tmp/merged

mkdir -p $tempdir
cd $rootdir/basis

for i in `ls -R | grep shp | sort | uniq`; do
    echo "Merging: " $i;
    for f in ./**/$i; do
        # Merge all unique shape files
        ogr2ogr -update -append $tempdir/$i $f -f "ESRI Shapefile";
    done;
done;

for d in $tempdir $rootdir/plus; do
    cd $d
    SRC_SHP_FILES=`find *.shp -type f`

    if [ "$SRC_SHP_FILES" ]; then

        PG="host=${DATABASE_PORT_5432_TCP_ADDR} port=5432 ACTIVE_SCHEMA=kbk10 user=${DB_USER} dbname=${DB_NAME} password=${DB_PASSWORD}"
        LCO="-lco SPATIAL_INDEX=ON -lco PRECISION=NO -lco LAUNDER=NO -lco GEOMETRY_NAME=geom"
        CONFIG="--config PG_USE_COPY YES"

        export PGCLIENTENCODING=UTF8;

        for SRC_SHP_FILE in $SRC_SHP_FILES; do

            # Load data into database
            echo "Importing: " $SRC_SHP_FILE;
            ogr2ogr -nlt PROMOTE_TO_MULTI -progress -skipfailures -overwrite -f "PostgreSQL" PG:"${PG}" ${CONFIG} -gt 65536 -s_srs "EPSG:28992" -t_srs "EPSG:28992" $SRC_SHP_FILE ${LCO} 2>&1 > /tmp/error_import.log

        done
    fi
done
