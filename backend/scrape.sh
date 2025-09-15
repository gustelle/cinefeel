#!/bin/bash

python3 main.py scrape

prefect deployment run "scrape_flow/wikipedia_scraping_movies" 
# prefect deployment run "scrape_flow/wikipedia_scraping_persons" 