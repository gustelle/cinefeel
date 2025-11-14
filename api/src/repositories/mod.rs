use rsmgclient::{ConnectParams, Connection, Value, SSLMode, ConnectionStatus, QueryParam};
use dotenv::dotenv;
use std::env;

use crate::interfaces::DbRepository;


pub struct MemgraphRepository {   
}

impl DbRepository for MemgraphRepository {

    fn connect(&self) -> bool {
        // Implementation for connecting to Memgraph
        true
    }

    fn disconnect(&self) -> bool {
        // Implementation for disconnecting from Memgraph
        true
    }

    fn query(&self, query: &str, params: Option<&[(&str, &str)]>) -> Option<Vec<String>> {
        dotenv().ok(); // Reads the .env file

        let host = env::var("GRAPHDB_HOST").unwrap_or("localhost".to_string());
        let db_port: String = env::var("GRAPHDB_PORT").unwrap_or("7687".to_string());
        let db_port: u16 = db_port.parse().unwrap_or(7687);

        // Connect to Memgraph 
        let connect_params = ConnectParams {
            host: Some(host),
            port: db_port,
            sslmode: SSLMode::Disable,
            ..Default::default()
        };
        let mut connection = Connection::connect(&connect_params).unwrap();
    
        // Check if connection is established.
        let status = connection.status();
        
        if status != ConnectionStatus::Ready {
            println!("Connection failed with status: {:?}", status);
            return None;
            
        } else {
            println!("Connection established with status: {:?}", status);
        }

        // transform the params into the required format
        // it must be a HashMap<String, QueryParam>
        let formatted_params = match params {
            Some(p) => {
                let mut map = std::collections::HashMap::new();
                for (key, value) in p.iter() {
                    map.insert(key.to_string(), QueryParam::String(value.to_string()));
                }
                map
            },
            None => std::collections::HashMap::new(),
        };
    
        // Fetch the graph.
        let _columns = connection.execute(query, Some(&formatted_params));

        let mut results = Vec::new();
        
        while let Ok(result) = connection.fetchall() {
            for record in result {
                for value in record.values {
                    match value {
                        Value::Node(node) => results.push(format!("Node: {}", node.properties.iter()
                            .map(|(k, v)| format!("{}: {}", k, v))
                            .collect::<Vec<String>>()
                            .join(", ") )),
                        Value::Relationship(edge) => results.push(format!("Edge: {}", edge.id)),
                        _ => {
                            results.push(format!("Other Value: {:?}", value));
                        }
                    }
                }
            }
            // Close the connection.
            connection.close();
        }
    
        return Some(results);
    }

}

pub fn query_memgraph(query: &str, params: Option<&[(&str, &str)]>) -> Option<Vec<String>> {
    let repo = MemgraphRepository{};
    repo.query(query, params)
}

