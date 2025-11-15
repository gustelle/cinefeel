use rsmgclient::{ConnectParams, Connection, Value, SSLMode, ConnectionStatus, QueryParam};
use dotenv::dotenv;
use std::env;
use std::collections::HashMap;

use crate::{entities::{Biography, Person, StorableEntity}, interfaces::DbRepository};


#[derive(Default, Debug, PartialEq)]
pub struct PersonRepository {   
}


impl DbRepository<Person> for PersonRepository {

    fn new() -> Self {
        dotenv().ok(); // Reads the .env file
        Default::default()
    }

    fn query(&self, query: &str, params: HashMap<String, String>) -> Option<Vec<Person>> {
        

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
        let formatted_params: HashMap<String, QueryParam> = params.into_iter().map(|(k, v)| {
            (k, QueryParam::String(v))
        }).collect();
    
        // Fetch the graph.
        let _columns = connection.execute(query, Some(&formatted_params));

        let mut results: Vec<Person> = Vec::new();
        
        while let Ok(result) = connection.fetchall() {
            for record in result {
                for value in record.values {
                    match value {
                        Value::Node(node) => results.push(
                            Person {
                                root: StorableEntity {
                                    uid: node.properties.get("uid").unwrap().to_string(),
                                    title: node.properties.get("title").unwrap().to_string(),
                                    permalink: node.properties.get("permalink").unwrap().to_string(),
                                },
                                biography: Biography {
                                    full_name: match node.properties.get("full_name") {
                                        Some(Value::String(name)) => Some(name.clone()),
                                        _ => None,
                                    }
                                }.into(),
                            }
                        ),
                        _ => {
                            return None
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


