#!/bin/bash

# TODO:
# check if services are running (prefect, etc) via a health check

python3 main.py connect

prefect deployment run "connection_flow/movies_connection" 
# prefect deployment run "connection_flow/persons_connection" 