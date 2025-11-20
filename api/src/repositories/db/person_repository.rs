use log::info;
use rsmgclient::{ConnectParams, Connection, Value, SSLMode, ConnectionStatus, QueryParam};
use dotenv::dotenv;
use std::env;
use std::collections::HashMap;

use crate::interfaces::db::DbRepository;
use crate::entities::person::{Person, Biography};
use crate::entities::storable::StorableEntity;


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
                        Value::Node(node) => {
                            //info!("Node properties: {:?}", node.properties);
                            results.push(
                            Person {
                                root: StorableEntity {
                                    uid: node.properties.get("uid").unwrap().to_string(),
                                    title: node.properties.get("title").unwrap().to_string(),
                                    permalink: node.properties.get("permalink").unwrap().to_string(),
                                },
                                biography: Biography {
                                    // complete the biography fields
                                    // if the property does not exist, set it to None
                                    full_name: node.properties.get("biography").and_then(|v| {
                                        match v {
                                            Value::Map(map) => {
                                                map.get("full_name").map(|v| v.to_string())
                                            },
                                            _ => None,
                                        }
                                    }),
                                    birth_date: node.properties.get("biography").and_then(|v| {
                                        match v {
                                            Value::Map(map) => {
                                                map.get("birth_date").map(|v| v.to_string())
                                            },
                                            _ => None,
                                        }
                                    }),
                                }.into(),
                            }
                        )},
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


