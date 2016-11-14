/* --------------------------------------------------
 Huisnummers

Derived from BGT/IMGeo, but not yet available from
Amsterdam BGT team so added by Webmapper

 --------------------------------------------------*/

ALTER TABLE teksten.bgt_nummeraanduidingreeks ADD COLUMN ogc_fid SERIAL PRIMARY KEY;
CREATE INDEX bgt_nummeraanduidingreeks_gix ON teksten.bgt_nummeraanduidingreeks USING GIST(geometrie);
CLUSTER teksten.bgt_nummeraanduidingreeks USING bgt_nummeraanduidingreeks_gix;
VACUUM ANALYZE teksten.bgt_nummeraanduidingreeks;

/* --------------------------------------------------
 Parken

Derived from TOP10NL 'functioneelgebied_punt' and using
'registratiefgebied_vlak' cut out Amsterdam area.

 --------------------------------------------------*/

CREATE TABLE
    teksten.functioneelgebied_punt
AS SELECT
    a.*
FROM
    top10nl.functioneelgebied_punt a,
    top10nl.registratiefgebied_vlak b
WHERE
    a.wkb_geometry && b.wkb_geometry
AND
    b.naamnl = '(1:Amsterdam)'
AND
    a.naamnl IS NOT NULL
AND
    a.typefunctioneelgebied = 'park';

ALTER TABLE teksten.functioneelgebied_punt ADD PRIMARY KEY (lokaalid);
ALTER TABLE teksten.functioneelgebied_punt ADD COLUMN naamnl_stripped varchar;
UPDATE teksten.functioneelgebied_punt SET naamnl_stripped = right(naamnl,-3);
UPDATE teksten.functioneelgebied_punt SET naamnl_stripped = left(naamnl_stripped,-1);
UPDATE teksten.functioneelgebied_punt SET naamnl = naamnl_stripped;
ALTER TABLE teksten.functioneelgebied_punt DROP COLUMN naamnl_stripped;
ALTER TABLE teksten.functioneelgebied_punt RENAME COLUMN wkb_geometry TO geometrie;
CREATE INDEX functioneelgebied_punt_gix ON teksten.functioneelgebied_punt USING GIST (geometrie);
CLUSTER teksten.functioneelgebied_punt USING functioneelgebied_punt_gix;
VACUUM ANALYZE teksten.functioneelgebied_punt;

/* --------------------------------------------------
 Dierentuinen

Derived from TOP10NL 'functioneelgebied_vlak' and using
'registratiefgebied_vlak' cut out Amsterdam area.

 --------------------------------------------------*/

CREATE TABLE
    teksten.functioneelgebied_vlak
AS SELECT
    a.*
FROM
    top10nl.functioneelgebied_vlak a,
    top10nl.registratiefgebied_vlak b
WHERE
    a.wkb_geometry && b.wkb_geometry
AND
    b.naamnl = '(1:Amsterdam)'
AND
    a.naamnl IS NOT NULL
AND
    a.typefunctioneelgebied = 'dierentuin, safaripark';

ALTER TABLE teksten.functioneelgebied_vlak ADD PRIMARY KEY (lokaalid);
ALTER TABLE teksten.functioneelgebied_vlak ADD COLUMN naamnl_stripped varchar;
UPDATE teksten.functioneelgebied_vlak SET naamnl_stripped = right(naamnl,-3);
UPDATE teksten.functioneelgebied_vlak SET naamnl_stripped = left(naamnl_stripped,-1);
UPDATE teksten.functioneelgebied_vlak SET naamnl = naamnl_stripped;
ALTER TABLE teksten.functioneelgebied_vlak DROP COLUMN naamnl_stripped;
ALTER TABLE teksten.functioneelgebied_vlak ADD COLUMN geometrie geometry(Point,28992);
UPDATE teksten.functioneelgebied_vlak SET geometrie = ST_Centroid(ST_Transform(wkb_geometry,28992));
ALTER TABLE teksten.functioneelgebied_vlak DROP COLUMN wkb_geometry;
CREATE INDEX functioneelgebied_vlak_gix ON teksten.functioneelgebied_vlak USING GIST (geometrie);
CLUSTER teksten.functioneelgebied_vlak USING functioneelgebied_vlak_gix;
VACUUM ANALYZE teksten.functioneelgebied_punt;


/* --------------------------------------------------
 Stations

1. Download 'https://geodata.nationaalgeoregister.nl/spoorwegen/wfs?request=GetFeature&service=WFS&version=2.0.0&typeName=spoorwegen:station&outputFormat=application/json&srsName=EPSG:4326'
2. Importeer tabel 'stations' in Postgres schema 'spoorwegen' mbv ogr2ogr

LET OP: output van WFS-request is in WGS-84!

 --------------------------------------------------*/

CREATE TABLE
    teksten.stations
AS SELECT
    a.ogc_fid,
    a.naam,
    ST_Transform(a.geometrie,28992) AS geometrie
FROM
    spoorwegen.stations a,
    top10nl.registratiefgebied_vlak b
WHERE
    ST_Transform(a.geometrie,28992) && b.wkb_geometry
AND
    b.naamnl = '(1:Amsterdam)';

ALTER TABLE teksten.stations ADD PRIMARY KEY (ogc_fid);
CREATE INDEX stations_gix ON teksten.stations USING GIST (geometrie);
CLUSTER teksten.stations USING stations_gix;
VACUUM ANALYZE teksten.stations;

/* --------------------------------------------------
 Plaatsnamen

Derived from TOP10NL 'plaats_vlak'
 
 --------------------------------------------------*/

CREATE TABLE teksten.plaats_vlak AS SELECT * FROM top10nl.plaats_vlak;
ALTER TABLE teksten.plaats_vlak ADD PRIMARY KEY (lokaalid);
ALTER TABLE teksten.plaats_vlak ADD COLUMN geometrie geometry(Point,28992);
UPDATE teksten.plaats_vlak SET geometrie = ST_Centroid(wkb_geometry);
UPDATE teksten.plaats_vlak SET geometrie = ST_Centroid(ST_ConvexHull(wkb_geometry)) WHERE NOT ST_Contains(wkb_geometry,geometrie);
UPDATE teksten.plaats_vlak SET geometrie = ST_PointOnSurface(wkb_geometry) WHERE NOT ST_Contains(wkb_geometry, geometrie);
ALTER TABLE teksten.plaats_vlak DROP COLUMN wkb_geometry;
CREATE INDEX plaats_vlak_idx ON teksten.plaats_vlak USING btree(typegebied);
CREATE INDEX plaats_vlak_gix ON teksten.plaats_vlak USING gist(geometrie);
CLUSTER teksten.plaats_vlak USING plaats_vlak_gix;
