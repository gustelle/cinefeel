

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
./scrape.sh

# 2. extract entities (movies, persons)
./extract.sh

# 3. store extracted entities into the graph DB & meili
./store.sh

# 4. connect entities between them
./connect.sh

# eventually vizualise the running flows on http://localhost:4200/

```

# How to test

```sh

pytest

```