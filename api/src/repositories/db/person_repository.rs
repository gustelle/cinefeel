
use log::info;
use rsmgclient::{ Node, QueryParam, Value};
use dotenv::dotenv;
use std::collections::HashMap;


use crate::interfaces::db::DbRepository;
use crate::entities::person::{Biography, Influences, Person};
use crate::entities::storable::StorableEntity;
use crate::repositories::db::connection::get_connection;

#[derive(Default)]
pub struct PersonRepository {
    
}

fn remove_quotes(s: &str) -> String {
    s.trim_matches(|c| c == '"' || c == '\'').to_string()
}

// converts a Value::Node into a Person entity
fn from_node(node: &Node) -> Person {
    
    Person {
        root: StorableEntity {
            uid: remove_quotes(&node.properties.get("uid").unwrap().to_string()),
            title: remove_quotes(&node.properties.get("title").unwrap().to_string()),
            permalink: remove_quotes(&node.properties.get("permalink").unwrap().to_string()),
        },
        biography: Biography {
            // complete the biography fields
            // if the property does not exist, set it to None
            full_name: node.properties.get("biography").and_then(|v| {
                match v {
                    Value::Map(map) => {
                        Some(remove_quotes(&map.get("full_name").unwrap().to_string()))
                    },
                    _ => None,
                }
            }),
            birth_date: node.properties.get("biography").and_then(|v| {
                match v {
                    Value::Map(map) => {
                        Some(remove_quotes(&map.get("birth_date").unwrap().to_string()))
                    },
                    _ => None,
                }
            }),
        }.into(),
        // a list of influences
        influences: Influences {
            persons: node.properties.get("influences").and_then(|v| {
                match v {
                    Value::Map(map) => {
                        map.get("persons").and_then(|val| {
                            match val {
                                Value::List(list) => {
                                    Some(list.iter().map(|item| item.to_string()).collect())
                                },
                                _ => None,
                            }
                        })
                    },
                    _ => None,
                }
            }),
            work_of_arts: node.properties.get("influences").and_then(|v| {
                match v {
                    Value::Map(map) => {
                        map.get("work_of_arts").and_then(|val| {
                            match val {
                                Value::List(list) => {
                                    Some(list.iter().map(|item| item.to_string()).collect())
                                },
                                _ => None,
                            }
                        })
                    },
                    _ => None,
                }
            }),
        }.into(),
    }
}


impl DbRepository<Person> for PersonRepository {

     fn new() -> Self {
        dotenv().ok(); // Reads the .env file
        Default::default()
    }


    fn query(&self, query: &str, params: HashMap<String, String>) -> Option<Vec<Person>> {

        info!("Executing query: {}", query);
        info!("With params: {:?}", params);

        // transform the params into the required format
        // it must be a HashMap<String, QueryParam>
        let formatted_params: HashMap<String, QueryParam> = params.into_iter().map(|(k, v)| {
            (k, QueryParam::String(v))
        }).collect();

        let mut _connection = get_connection()?;
    
        // Fetch the graph.
        let _columns = _connection.execute(query, Some(&formatted_params));

        let mut results: Vec<Person> = Vec::new();
        
        while let Ok(result) = _connection.fetchall() {
            info!("Fetched {} records", result.len());
            for record in result {
                for value in record.values {
                    match value {
                        Value::Node(node) => {
                            //info!("Node properties: {:?}", node.properties);
                            results.push(
                                from_node(&node)
                            );
                        },
                        _ => {
                            return None
                        }
                    }
                }
            }
        }
        // Close the connection.
        _connection.close();
    
        return Some(results);
    }

}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_root_data() {
        // Test from_node function
        let mut properties = HashMap::new();
        properties.insert("uid".to_string(), Value::String("123".to_string()));
        properties.insert("title".to_string(), Value::String("John Doe".to_string()));
        properties.insert("permalink".to_string(), Value::String("john-doe".to_string()));
        let node = Node {
            id: 1,
            labels: vec!["Person".to_string()],
            properties,
            label_count: 1,
        };
        let person = from_node(&node);
        assert_eq!(person.root.uid, "123");
        assert_eq!(person.root.title, "John Doe");
        assert_eq!(person.root.permalink, "john-doe");
    }

    #[test]
    fn test_with_biography() {
        // Test from_node function with biography
        let mut bio_map = HashMap::new();
        bio_map.insert("full_name".to_string(), Value::String("Johnathan Doe".to_string()));
        bio_map.insert("birth_date".to_string(), Value::String("1990-01-01".to_string()));
        
        let mut properties = HashMap::new();
        properties.insert("uid".to_string(), Value::String("123".to_string()));
        properties.insert("title".to_string(), Value::String("John Doe".to_string()));
        properties.insert("permalink".to_string(), Value::String("john-doe".to_string()));
        properties.insert("biography".to_string(), Value::Map(bio_map));
        
        let node = Node {
            id: 1,
            labels: vec!["Person".to_string()],
            properties,
            label_count: 1,
        };
        let person = from_node(&node);
        assert_eq!(person.biography.as_ref().unwrap().full_name.as_ref().unwrap(), "Johnathan Doe");
        assert_eq!(person.biography.as_ref().unwrap().birth_date.as_ref().unwrap(), "1990-01-01");
    }
}