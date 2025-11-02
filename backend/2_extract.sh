#!/bin/bash

# TODO:
# check if services are running (prefect, etc) via a health check

python3 main.py extract

prefect deployment run "extract_entities_flow/persons_extraction" 
prefect deployment run "extract_entities_flow/movies_extraction" 