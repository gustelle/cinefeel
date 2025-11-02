#!/bin/bash

docker compose up -d

# set API url
prefect config set PREFECT_API_URL="http://localhost:4200/api"  

# enable task result caching
# see https://docs.prefect.io/v3/concepts/caching
prefect config set PREFECT_RESULTS_PERSIST_BY_DEFAULT=true

# ********************************
# global concurrency limit 
# ********************************
# delete existing limit if any
prefect --no-prompt gcl delete cinefeel
# slot_decay_per_second is mandatory to use rate_limit in tasks
# slot_decay_per_second of 2.0 means that every 0.5 second, a slot is freed
# see https://docs.prefect.io/v3/concepts/global-concurrency-limits#slot-decay
prefect gcl create cinefeel --limit 10 --slot-decay-per-second 2.0

# concurrent tasks

# *********************************
# heavy tasks limit (e.g., extractors)
# *********************************
prefect config set PREFECT_TASK_RUN_TAG_CONCURRENCY_SLOT_WAIT_SECONDS=10
prefect --no-prompt concurrency-limit delete heavy  # in case it already exists
prefect concurrency-limit create heavy 10


# *********************************
# scraping tasks limit
# *********************************
prefect --no-prompt concurrency-limit delete scraping  # in case it already exists
prefect concurrency-limit create scraping 20 
# ************************************************************
# API Calls
# ************************************************************
# api-rate-limiting policy must be declared in the UI
# because Prefect CLI does not support setting the slot_decay_per_second parameter yet
# prefect --no-prompt concurrency-limit delete api-rate-limiting  # in case it already exists
# prefect concurrency-limit create api-rate-limiting 5 

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