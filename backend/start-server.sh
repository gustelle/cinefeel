#!/bin/bash

docker compose up -d

# set API url
prefect config set PREFECT_API_URL="http://localhost:4200/api"  

# enable task result caching
# see https://docs.prefect.io/v3/concepts/caching
prefect config set PREFECT_RESULTS_PERSIST_BY_DEFAULT=true

# apply concurrency limit for workers (flows)
prefect gcl create cinefeel --limit 5 --slot-decay-per-second 1.0

# create a work pool (for flows)
prefect work-pool create "local-processes" --type process 

# default work pool
prefect config set PREFECT_DEFAULT_WORK_POOL_NAME="local-processes"

# set concurrency limit for the work pool
prefect work-pool set-concurrency-limit "local-processes" 8 

# make sure to remove stale tasks
# see https://github.com/PrefectHQ/prefect/issues/5995
prefect concurrency-limit reset cinefeel_tasks

# for concurrent tasks
prefect concurrency-limit create cinefeel_tasks 20

#prefect worker start --pool "local-processes" #--work-queue "local-queue"

prefect worker start --pool "local-processes" --work-queue "default"