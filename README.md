# atlas_kbk
Atlas import docker for Kleinschalige Basiskaart 10, Kleinschalige Basiskaart 50 en BGT

## 1. Objectstore

De basiskaart shapes worden geladen vanaf de objectstore. 
Zie voor de aanlog informatie src/objectstore/objectstore. 
BGT wordt aangemaakt via FME scripts die de shapes als een zip file naar een directory shapes schrijft. 
Het script zoekt vervolgens naar een file die eindigt met latest.zip en begint met Export_Shapes_Totaalgebied. 
Die zip file wordt hier verwerkt
KBK10 en KBK50 worden handmatig in de directory gezet. 
Het script zoekt in de mappen diva/kbka10 en diva/kbka50. 
Alle zips die daar gevonden worden worden gebruikt om de databases op te bouwen.

## 2. Resultaat

Er worden onder database "basiskaart" 3 schema's gemaakt: kbk10, kbk50 en bgt. 
Alle shapes die gevonden zijn in de zips zijn één op één vertaald naar tabellen in de verschillende schema's. 
Daarnaast zijn de kolommen hernoemd naar de originele waarden, omdat ze afgekort zijn in het proces 

Voor BGT worden daarnaast views gemaakt die zijn gebaseerd op een spreadsheet zoals terug te vinden in basiskaart/fixtures. 
Het script tolereert ontbrekende tabellen en kolommen in de shape tabellen.

### run import in docker lokaal

- de import gebruikt de ogr2ogr binary die geinstalleerd is in de Linux container

- de import leest grote bestanden (Esri_Shape_totaal-latest.zip is 2 GB)
    dus je docker runner heeft >3 GB memory nodig.
    

 ### run database import
- export GOB_OBJECTSTORE_PASSWORD=xxxx
- export BGT_OBJECTSTORE_PASSWORD=xxxx
- docker-compose up -d --build

### show log
- docker-compose logs -f importer

### run tests
- docker-compose run importer pytest

