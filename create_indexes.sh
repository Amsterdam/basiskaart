#!/usr/bin/env bash

psql -h ${DATABASE_PORT_5432_TCP_ADDR} -U ${DB_USER} -d basiskaart -f indexes.sql
