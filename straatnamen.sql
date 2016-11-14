CREATE SCHEMA IF NOT EXISTS top10nl;
CREATE SCHEMA IF NOT EXISTS nwb;
CREATE SCHEMA IF NOT EXISTS teksten;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

/* Nationaal Wegen Bestand (NWB) wegvakken voor Amsterdam en zonder bruggen of genummerde opritten/afritten

1. Download 'http://geodata.nationaalgeoregister.nl/nwbwegen/extract/nwbwegen.zip'
2. Importeer 'nwb-wegen/geogegevens/shapefile/nederland_totaal/Wegvakken/Wegvakken.shp' in Postgres schema 'nwb' mbv ogr2ogr
3. Importeer TOP10NL in Postgres schema 'top10nl' mbv NLExtract

NWB kan ge-clipped worden door het attribuut gme_naam (gemeente naam) te gebruiken. Ook worden alle bruggen niet mee genomen. Bruggen worden in uppercase 'BRUG' geschreven en kunnen daarom makkelijk eruit worden gefilterd.

*/
DROP TABLE IF EXISTS public.ams_wvk3 CASCADE;
CREATE TABLE public.ams_wvk3 AS
    SELECT
        (ST_DUMP(geom)).geom AS geom,
        a.stt_naam AS straatnaam,
        a.wvk_id,
        a.ogc_fid
    FROM
        nwb.wegvakken a
    WHERE
        a.gme_naam = 'Amsterdam'
        AND a.stt_naam = trim(trailing '1,2,3,4,5,6,7,8,9,0' from a.stt_naam) 
        AND a.stt_naam !~ '.*BRUG*'
;

/*Hartlijnen (TOP10NL) clip op Amsterdam*/
DROP TABLE IF EXISTS public.hartlijnen_ams CASCADE;
CREATE TABLE public.hartlijnen_ams AS
	SELECT 
	    a.*
	FROM 
	    top10nl.wegdeel_hartlijn a,
	    top10nl.registratiefgebied_vlak b
	WHERE
	    b.naamofficieel = 'Amsterdam' AND
	    ST_Intersects(a.wkb_geometry, b.wkb_geometry)
;

/*WegdeelVlak (TOP10NL) met namen van de NWB*/
DROP TABLE IF EXISTS public.vlak_top10_1 CASCADE;
CREATE TABLE public.vlak_top10_1 AS
	SELECT
	    ST_Length(ST_Intersection(a.geom, b.wkb_geometry)) AS lengte,
	    a.straatnaam,
	    b.lokaalid,
	    b.wkb_geometry AS geom
	FROM
	    public.ams_wvk3 a,
	    top10nl.wegdeel_vlak b
	WHERE 
	    ST_Intersects( a.geom, b.wkb_geometry)
;

/*WegdeelVlak (TOP10NL) met totale lente van de lijnen met dezelfde naam*/
DROP TABLE IF EXISTS public.vlak_top10_2 CASCADE;
CREATE TABLE public.vlak_top10_2 AS
	SELECT 
	    a.straatnaam,
	    a.lokaalid,
	    sum(a.lengte) as lengte,
	    a.geom
	FROM 
	    public.vlak_top10_1 AS a
	GROUP BY a.straatnaam, a.lokaalid, a.geom
;

/*Selecteer WegdeelVlak (TOP10NL) met de naam van maximale lengte lijn */
DROP TABLE IF EXISTS public.vlak_top10_3 CASCADE;
CREATE TABLE public.vlak_top10_3 AS
	SELECT 
	    a.straatnaam,
	    a.lokaalid,
	    a.geom
	FROM 
	    public.vlak_top10_2 a,
	    (SELECT lokaalid, max(lengte) as lengte FROM public.vlak_top10_2 group by lokaalid) b
	WHERE
	    a.lengte = b.lengte
;

/*Left Outer Join WegdeelVlak met Hartlijn (TOP10NL) op lokaal ID */
DROP TABLE IF EXISTS public.hartlijn_1 CASCADE;
CREATE TABLE public.hartlijn_1 AS
	SELECT
	    a.lokaalid,
	    a.typeweg,
	    a.typeinfrastructuur,
	    a.hoofdverkeersgebruik,
	    a.fysiekvoorkomen,
	    a.verhardingsbreedteklasse,
	    a.naam,
	    a.awegnummer,
	    a.nwegnummer,
	    a.ewegnummer,
	    a.swegnummer,
	    a.afritnummer,
	    a.afritnaam,
	    a.knooppuntnaam,
	    a.brugnaam,
	    a.tunnelnaam,
	    b.straatnaam,
	    a.wkb_geometry
	FROM 
	    public.hartlijnen_ams AS a
	LEFT OUTER JOIN public.vlak_top10_3 AS b
	ON (a.lokaalid = b.lokaalid)
;

/*Topology verberteren*/

SELECT topology.DropTopology('hartlijn_topo'); 
SELECT topology.CreateTopology('hartlijn_topo', 28992);
SELECT topology.AddTopoGeometryColumn('hartlijn_topo', 'public', 'hartlijn_1', 'topo_geom', 'LINESTRING');
UPDATE public.hartlijn_1 SET topo_geom = topology.toTopoGeom(wkb_geometry, 'hartlijn_topo', 1, 0.1);

DROP TABLE IF EXISTS public.hartlijn_clean CASCADE;
CREATE TABLE public.hartlijn_clean AS (
    SELECT  
    a.lokaalid,
    a.typeweg,
    a.typeinfrastructuur,
    a.hoofdverkeersgebruik,
    a.fysiekvoorkomen,
    a.verhardingsbreedteklasse,
    a.naam,
    a.awegnummer,
    a.nwegnummer,
    a.ewegnummer,
    a.swegnummer,
    a.afritnummer,
    a.afritnaam,
    a.knooppuntnaam,
    a.brugnaam,
    a.tunnelnaam,
    a.straatnaam,
    (ST_Dump(a.topo_geom)).geom::geometry(LINESTRING,28992) AS geom
    FROM public.hartlijn_1 AS a
);

/*Opknippen lijnen*/

DROP TABLE IF EXISTS public.punten_hartlijn CASCADE;
CREATE TABLE public.punten_hartlijn 
AS
SELECT 
    lokaalid,
    ST_Multi(ST_Collect(f.the_geom)) as the_geom
FROM (SELECT lokaalid, (ST_DumpPoints(geom)).geom As the_geom
      FROM public.hartlijn_clean WHERE straatnaam IS NOT NULL ) As f
GROUP BY lokaalid;




/*Functie van http://gis.stackexchange.com/questions/112282/split-lines-into-non-overlapping-subsets-based-on-points*/
DROP FUNCTION IF EXISTS split_line_multipoint(input_geom geometry, blade geometry);
CREATE FUNCTION split_line_multipoint(input_geom geometry, blade geometry)
  RETURNS geometry AS
$BODY$
    -- this function is a wrapper around the function ST_Split 
    -- to allow splitting multilines with multipoints
    --
    DECLARE
        result geometry;
        simple_blade geometry;
        blade_geometry_type text := GeometryType(blade);
        geom_geometry_type text := GeometryType(input_geom);
    BEGIN
        IF blade_geometry_type NOT ILIKE 'MULTI%' THEN
            RETURN ST_Split(input_geom, blade);
        ELSIF blade_geometry_type NOT ILIKE '%POINT' THEN
            RAISE NOTICE 'Need a Point/MultiPoint blade';
            RETURN NULL;
        END IF;

        IF geom_geometry_type NOT ILIKE '%LINESTRING' THEN
            RAISE NOTICE 'Need a LineString/MultiLineString input_geom';
            RETURN NULL;
        END IF;

        result := input_geom;           
        -- Loop on all the points in the blade
        FOR simple_blade IN SELECT (ST_Dump(ST_CollectionExtract(blade, 1))).geom
        LOOP
            -- keep splitting the previous result
            result := ST_CollectionExtract(ST_Split(result, simple_blade), 2);
        END LOOP;
        RETURN result;
    END;
$BODY$
LANGUAGE plpgsql IMMUTABLE;

DROP TABLE IF EXISTS public.hartlijn_1b CASCADE;
CREATE TABLE public.hartlijn_1b 
AS
SELECT 
    (ST_Dump(split_line_multipoint(a.geom, b.the_geom))).geom::geometry(LINESTRING,28992) AS geom,
    a.straatnaam,
    a.lokaalid,
    a.typeweg,
    a.typeinfrastructuur,
    a.hoofdverkeersgebruik,
    a.fysiekvoorkomen,
    a.verhardingsbreedteklasse,
    a.naam,
    a.awegnummer,
    a.nwegnummer,
    a.ewegnummer,
    a.swegnummer,
    a.afritnummer,
    a.afritnaam,
    a.knooppuntnaam,
    a.brugnaam,
    a.tunnelnaam
    FROM public.hartlijn_clean AS a,
        public.punten_hartlijn AS b
    WHERE a.lokaalid = b.lokaalid
        UNION ALL
        SELECT 
        a.geom AS geom,
        a.straatnaam,
        a.lokaalid,
        a.typeweg,
        a.typeinfrastructuur,
        a.hoofdverkeersgebruik,
        a.fysiekvoorkomen,
        a.verhardingsbreedteklasse,
        a.naam,
        a.awegnummer,
        a.nwegnummer,
        a.ewegnummer,
        a.swegnummer,
        a.afritnummer,
        a.afritnaam,
        a.knooppuntnaam,
        a.brugnaam,
        a.tunnelnaam
        FROM 
            public.hartlijn_clean AS a
        WHERE straatnaam IS NULL; 


/*Doorlopende straat = dezelfde naam*/
DROP TABLE IF EXISTS public.hartlijn_2 CASCADE;
WITH pre AS 
(
    SELECT 
        b.straatnaam AS straatnaam,
        a.lokaalid,
        a.typeweg,
        a.typeinfrastructuur,
        a.hoofdverkeersgebruik,
        a.fysiekvoorkomen,
        a.verhardingsbreedteklasse,
        a.naam,
        a.awegnummer,
        a.nwegnummer,
        a.ewegnummer,
        a.swegnummer,
        a.afritnummer,
        a.afritnaam,
        a.knooppuntnaam,
        a.brugnaam,
        a.tunnelnaam,
        ABS((ST_Azimuth(ST_Startpoint(a.geom),ST_Endpoint(a.geom))/(2*pi())*360)-(ST_Azimuth(ST_Startpoint(b.geom),ST_Endpoint(b.geom))/(2*pi())*360)) AS A_lijn,
        a.geom AS geoma,
        b.geom AS geomb        
    FROM 
        public.hartlijn_1b AS a,
        (SELECT * FROM public.hartlijn_1b) AS b
    WHERE 
            ST_Intersects(a.geom,b.geom) 
            AND (a.straatnaam IS NULL AND b.straatnaam IS NOT NULL) 
            AND (a.typeweg = b.typeweg) 
            AND (a.hoofdverkeersgebruik = b.hoofdverkeersgebruik)
)
SELECT
    pre.geoma AS geom,
    pre.straatnaam,
    pre.lokaalid,
    pre.typeweg,
    pre.typeinfrastructuur,
    pre.hoofdverkeersgebruik,
    pre.fysiekvoorkomen,
    pre.verhardingsbreedteklasse,
    pre.naam,
    pre.awegnummer,
    pre.nwegnummer,
    pre.ewegnummer,
    pre.swegnummer,
    pre.afritnummer,
    pre.afritnaam,
    pre.knooppuntnaam,
    pre.brugnaam,
    pre.tunnelnaam
INTO 
    public.hartlijn_2
FROM 
    pre
WHERE 
    (pre.A_lijn < 10 AND pre.A_lijn > 0) OR ( pre.A_lijn < 190 AND pre.A_lijn > 170) OR ( pre.A_lijn <= 360 AND pre.A_lijn > 350)
;

/*update 1b met de nieuwe info*/
UPDATE public.hartlijn_1b AS a
SET straatnaam = b.straatnaam FROM 
public.hartlijn_2 AS b 
WHERE ST_Equals(a.geom, b.geom) AND a.straatnaam IS NULL ;

DROP TABLE IF EXISTS public.hartlijn_3 CASCADE;
WITH pre AS 
(
    SELECT 
        b.straatnaam AS straatnaam,
        a.lokaalid,
        a.typeweg,
        a.typeinfrastructuur,
        a.hoofdverkeersgebruik,
        a.fysiekvoorkomen,
        a.verhardingsbreedteklasse,
        a.naam,
        a.awegnummer,
        a.nwegnummer,
        a.ewegnummer,
        a.swegnummer,
        a.afritnummer,
        a.afritnaam,
        a.knooppuntnaam,
        a.brugnaam,
        a.tunnelnaam,
        ABS((ST_Azimuth(ST_Startpoint(a.geom),ST_Endpoint(a.geom))/(2*pi())*360)-(ST_Azimuth(ST_Startpoint(b.geom),ST_Endpoint(b.geom))/(2*pi())*360)) AS A_lijn,
        a.geom AS geoma,
        b.geom AS geomb        
    FROM 
        public.hartlijn_1b AS a,
        (SELECT * FROM public.hartlijn_1b) AS b
    WHERE 
        ST_Intersects(a.geom,b.geom) 
            AND (a.straatnaam IS NULL AND b.straatnaam IS NOT NULL) 
            AND (a.typeweg = b.typeweg) 
            AND (a.hoofdverkeersgebruik = b.hoofdverkeersgebruik)
)
SELECT
    pre.geoma AS geom,
    pre.straatnaam,
    pre.lokaalid,
    pre.typeweg,
    pre.typeinfrastructuur,
    pre.hoofdverkeersgebruik,
    pre.fysiekvoorkomen,
    pre.verhardingsbreedteklasse,
    pre.naam,
    pre.awegnummer,
    pre.nwegnummer,
    pre.ewegnummer,
    pre.swegnummer,
    pre.afritnummer,
    pre.afritnaam,
    pre.knooppuntnaam,
    pre.brugnaam,
    pre.tunnelnaam
INTO 
    public.hartlijn_3
FROM 
    pre
WHERE 
    (pre.A_lijn < 10 AND pre.A_lijn > 0) OR ( pre.A_lijn < 190 AND pre.A_lijn > 170) OR ( pre.A_lijn <= 360 AND pre.A_lijn > 350)
;

UPDATE public.hartlijn_1b AS a
SET straatnaam = b.straatnaam FROM 
public.hartlijn_3 AS b 
WHERE ST_Equals(a.geom, b.geom) AND a.straatnaam IS NULL ;


/*Voeg lijnen die aan elkaar liggen met dezelfde naam samen*/

DROP TABLE IF EXISTS public.hartlijn_1c CASCADE;
CREATE TABLE public.hartlijn_1c AS
    SELECT
        straatnaam,
        typeweg,
        typeinfrastructuur,
        hoofdverkeersgebruik,
        verhardingsbreedteklasse,
        awegnummer,
        nwegnummer,
        ewegnummer,
        swegnummer,
        afritnummer,
        afritnaam,
        knooppuntnaam,
        brugnaam,
        tunnelnaam,
        (ST_Dump(geom)).geom AS geom,
        ST_Length(geom) AS lengte
    FROM 
        (SELECT 
            ST_LineMerge(ST_Union(geom)) AS geom, 
            straatnaam,
            typeweg,
            typeinfrastructuur,
            hoofdverkeersgebruik,
            verhardingsbreedteklasse,
            awegnummer,
            nwegnummer,
            ewegnummer,
            swegnummer,
            afritnummer,
            afritnaam,
            knooppuntnaam,
            brugnaam,
            tunnelnaam         
        FROM public.hartlijn_1b
        GROUP BY 
            straatnaam,
            typeweg,
            typeinfrastructuur,
            hoofdverkeersgebruik,
            verhardingsbreedteklasse,
            awegnummer,
            nwegnummer,
            ewegnummer,
            swegnummer,
            afritnummer,
            afritnaam,
            knooppuntnaam,
            brugnaam,
            tunnelnaam )
         AS street_union;

/*Lengte per lijn toevoegen*/


DROP TABLE IF EXISTS teksten.straatnamen CASCADE;
CREATE TABLE teksten.straatnamen AS
    SELECT
        straatnaam,
        typeweg,
        typeinfrastructuur,
        hoofdverkeersgebruik,
        verhardingsbreedteklasse,
        awegnummer,
        nwegnummer,
        ewegnummer,
        swegnummer,
        afritnummer,
        afritnaam,
        knooppuntnaam,
        brugnaam,
        tunnelnaam,
        lengte,
        ST_Length(geom) AS lengte_ind,
        (ST_Dump(geom)).geom::geometry(LineString,28992) AS geometrie
    FROM public.hartlijn_1c ;

ALTER TABLE teksten.straatnamen ADD COLUMN ogc_fid SERIAL PRIMARY KEY;
CREATE INDEX straatnamen_gix ON teksten.straatnamen USING gist(geometrie);
CLUSTER teksten.straatnamen USING straatnamen_gix;
CREATE INDEX straatnamen_idx ON teksten.straatnamen USING btree (typeweg);
CREATE INDEX straatnamen_idx2 ON teksten.straatnamen USING btree (lengte);
