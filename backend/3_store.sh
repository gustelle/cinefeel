#!/bin/bash

# TODO:
# check if services are running (prefect, etc) via a health check

python3 main.py store

prefect deployment run "db_storage_flow/movies_storage" 
prefect deployment run "db_storage_flow/persons_storage" 