

# Dependencies

- Ollama or mistral.ai account
- Redis 8
- Memgraph
- Prefect

# Install

```sh

poetry install 

```

# Start the service

```sh

# start prefect and all required services
./start-server.sh

# then open a new tab 
# 1. scrape data
./1_scrape.sh

# 2. extract entities (movies, persons)
./2_extract.sh

# 3. store extracted entities into the graph DB & meili
./3_store.sh

# 4. connect entities between them
./4_connect.sh

# eventually vizualise the running flows on http://localhost:4200/

```

# How to test

```sh

pytest

```

# About the stack used

We have tried various techniques and frameworks for NLP tasks like summarization and similarity search.
For similarity search, `txtai` is OK in terms of results and performance, but for summarization we preferred to use [Bert Extractive Summarizer](https://pypi.org/project/bert-extractive-summarizer/) which has much better quality/perf ratio than `BART`, the performance of which makes it unusable on a simple Macbook M2 with a decent RAM config.