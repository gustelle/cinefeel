


mod repositories;
mod interfaces;
mod entities;

use std::collections::HashMap;

use crate::{interfaces::{DbRepository}, repositories::{PersonRepository}};
 
fn main() {
    
    let repo = PersonRepository::new();

    let mut params = HashMap::new();
    params.insert("title".to_string(), "Lucien Nonguet".to_string());

    let results = repo.query("MATCH (n: Person {title: $title}) RETURN n;", params);

    match results {
        Some(records) => {
            for record   in records {
                println!("{}", record);
                
            }
        },
        None => println!("No results found or query failed."),
    }
}

