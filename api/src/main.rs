


mod repositories;
mod interfaces;
mod entities;

use std::collections::HashMap;
use actix_web::{get, post, web, App, HttpResponse, HttpServer, Responder};

use crate::{interfaces::{DbRepository}, repositories::{PersonRepository}};


#[get("/hello")]
async fn hello() -> impl Responder {

    let repo = PersonRepository::new();

    let mut params = HashMap::new();
    params.insert("title".to_string(), "Lucien Nonguet".to_string());

    let results = repo.query("MATCH (n: Person {title: $title}) RETURN n;", params);

    let mut response = "Results:\n".to_string();

    match results {
        Some(records) => {
            for record   in records {
                response.push_str(&format!("{}\n", record));
            }
        },
        None => {
            response.push_str("No records found.\n");
        }
    }

    HttpResponse::Ok().body(response)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .service(hello)
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}

 

