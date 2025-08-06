#!/bin/bash

poe deploy

prefect deployment run "batch_extraction_flow/wikipedia_movies_extraction" 
prefect deployment run "batch_extraction_flow/wikipedia_persons_extraction" 