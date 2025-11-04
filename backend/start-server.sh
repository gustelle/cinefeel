#!/bin/bash

docker compose up -d

# set API url
prefect config set PREFECT_API_URL="http://localhost:4200/api"  

# enable task result caching
# see https://docs.prefect.io/v3/concepts/caching
prefect config set PREFECT_RESULTS_PERSIST_BY_DEFAULT=true

# ********************************
# global concurrency limit and rate limiting
# ********************************
# delete existing limit if any
prefect --no-prompt gcl delete resource-rate-limiting
prefect gcl create resource-rate-limiting --limit 10 --slot-decay-per-second 2.0

prefect --no-prompt gcl delete api-rate-limiting
prefect gcl create api-rate-limiting --limit 10 --slot-decay-per-second 2.0
# ************************************************************

# concurrent tasks

# *********************************
# heavy tasks limit (e.g., extractors)
# *********************************
prefect --no-prompt concurrency-limit delete heavy  # in case it already exists
prefect concurrency-limit create heavy 20


# *********************************
# scraping tasks limit
# *********************************
prefect --no-prompt concurrency-limit delete scraping  # in case it already exists
prefect concurrency-limit create scraping 20 
# ************************************************************

# start server
# ************************************************************
# make sure to remove stale tasks

# create a work pool (for flows)
prefect work-pool create "local-processes" --type process 

# default work pool
prefect config set PREFECT_DEFAULT_WORK_POOL_NAME="local-processes"

# set concurrency limit for the work pool
prefect work-pool set-concurrency-limit "local-processes" 20

prefect worker start --pool "local-processes" --work-queue "default"