



mod repositories;
mod interfaces;

use crate::repositories::query_memgraph;
 
fn main() {
    
    let results = query_memgraph("MATCH (n: Person {title: $title}) RETURN n;", Some(&[("title", "Lucien Nonguet")]));

    match results {
        Some(records) => {
            for record in records {
                println!("{}", record);
            }
        },
        None => println!("No results found or query failed."),
    }
}