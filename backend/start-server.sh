#!/bin/bash

docker compose up -d

# set API url
prefect config set PREFECT_API_URL="http://localhost:4200/api"  

# enable task result caching
# see https://docs.prefect.io/v3/concepts/caching
prefect config set PREFECT_RESULTS_PERSIST_BY_DEFAULT=true

# apply concurrency limit for workers (flows)
prefect gcl create cinefeel --limit 10 --slot-decay-per-second 1.0

# create a work pool (for flows)
prefect work-pool create "local-processes" --type process 

prefect config set PREFECT_DEFAULT_WORK_POOL_NAME="local-processes"

# below 10, nothing will run
prefect work-pool set-concurrency-limit "local-processes" 8

# for concurrent tasks
prefect concurrency-limit create cinefeel_tasks 5

prefect worker start --pool "local-processes" #--work-queue "local-queue"

