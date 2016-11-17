#!/usr/bin/env bash

sleep 5

echo ${DATABASE_PORT_5432_TCP_ADDR}:5432:*:${DB_USER}:${DB_PASSWORD} > ~/.pgpass
chmod 600 ~/.pgpass
createdb -h ${DATABASE_PORT_5432_TCP_ADDR} -U ${DB_USER} ${DB_NAME}
psql -h ${DATABASE_PORT_5432_TCP_ADDR} -U ${DB_USER} -d basiskaart -c "create schema kbk10"
psql -h ${DATABASE_PORT_5432_TCP_ADDR} -U ${DB_USER} -d basiskaart -c "create schema kbk50"
psql -h ${DATABASE_PORT_5432_TCP_ADDR} -U ${DB_USER} -d basiskaart -c "create schema bgt"
