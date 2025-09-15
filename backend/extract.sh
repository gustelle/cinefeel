#!/bin/bash

python3 main.py extract

prefect deployment run "extract_entities/movies_extraction" 
# prefect deployment run "extract_entities/persons_extraction" 