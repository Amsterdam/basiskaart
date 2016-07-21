CREATE OR REPLACE FUNCTION geoindex(IN _schema TEXT)
RETURNS void
LANGUAGE plpgsql
AS
$$
DECLARE
   row     record;
BEGIN
   FOR row IN
       SELECT f_table_name FROM public.geometry_columns WHERE f_table_schema = _schema
   LOOP
       EXECUTE 'CREATE INDEX "' || row.f_table_name || '_gix" ON ' || _schema || '.' || quote_ident(row.f_table_name) || ' USING GIST(geom)';
       EXECUTE 'CLUSTER ' || _schema || '.' || quote_ident(row.f_table_name) || ' USING "' || row.f_table_name || '_gix"';
       EXECUTE 'ANALYZE ' || _schema || '.' || quote_ident(row.f_table_name);
       RAISE INFO 'Created index: %', row.f_table_name || '_gix';
   END LOOP;
END;
$$;

SELECT geoindex('kbk10');
SELECT geoindex('kbk50');
