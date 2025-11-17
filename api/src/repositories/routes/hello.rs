

use actix_web::{get, HttpResponse, Responder};
use juniper::Variables;

use crate::{repositories::query::person_schema::{create_schema}}; 



#[get("/hello")]
async fn hello() -> impl Responder {

    // let results = repo.query("MATCH (n: Person {title: $title}) RETURN n;", params);
    let schema = create_schema();

    // Run the execution.
    let (res, _errors) = juniper::execute_sync(
        "query { members(title: \"Lucien Nonguet\") { title } }",
        None,
        &schema,
        &Variables::new(),
        &(),
    ).unwrap();


    match res {
        juniper::Value::Object(obj) => {
            return HttpResponse::Ok().json(obj)
        },
        _ => {
            return HttpResponse::NoContent().finish()
        }
    }

    
}