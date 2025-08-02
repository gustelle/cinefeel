#!/bin/bash

# set API url
prefect config set PREFECT_API_URL="http://localhost:4200/api"  

# enable task result caching
# see https://docs.prefect.io/v3/concepts/caching
prefect config set PREFECT_RESULTS_PERSIST_BY_DEFAULT=true

# apply concurrency limit
prefect gcl create cinefeel --limit 10 --slot-decay-per-second 1.0

# create a work pool
prefect work-pool create "local-processes" --type process 

prefect config set PREFECT_DEFAULT_WORK_POOL_NAME="local-processes"

# apply a rate limit to the work pool
prefect work-pool set-concurrency-limit "local-processes" 10

prefect worker start --pool "local-processes" 

# react to events emitted 
# prefect automation create --from-file automation.yaml
# prefect deploy --prefect-file prefect.yaml