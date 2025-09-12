

# Dependencies

- Ollama or mistral.ai account
- Redis 8 
- Memgraph
- Prefect

# Start the service

```sh

# start prefect and all required services
./start-server.sh

# launch the flows in another tab
./run-flows.sh

# eventually vizualise the running flows on http://localhost:4200/

```

# How to test

```sh

poe test 

```