#!/bin/bash

docker compose up -d

# set API url
prefect config set PREFECT_API_URL="http://localhost:4200/api"  

# enable task result caching
# see https://docs.prefect.io/v3/concepts/caching
prefect config set PREFECT_RESULTS_PERSIST_BY_DEFAULT=true

# apply concurrency limit for workers (flows)
prefect gcl create cinefeel --limit 10 --slot-decay-per-second 1.0

# concurrent tasks
prefect config set PREFECT_TASK_RUN_TAG_CONCURRENCY_SLOT_WAIT_SECONDS=60
prefect --no-prompt concurrency-limit delete heavy  # in case it already exists
prefect concurrency-limit create heavy 2

prefect --no-prompt concurrency-limit delete scraping  # in case it already exists
prefect concurrency-limit create scraping 20

# start server
# ************************************************************
# make sure to remove stale tasks

# create a work pool (for flows)
prefect work-pool create "local-processes" --type process 

# default work pool
prefect config set PREFECT_DEFAULT_WORK_POOL_NAME="local-processes"

# set concurrency limit for the work pool
prefect work-pool set-concurrency-limit "local-processes" 8 

prefect worker start --pool "local-processes" --work-queue "default"