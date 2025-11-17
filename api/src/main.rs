


mod repositories;
mod interfaces;
mod entities;


use actix_web::{App, HttpServer};


use crate::repositories::routes::hello::hello;


#[actix_web::main]
async fn main() -> std::io::Result<()> {

    dotenv::dotenv().ok();
    env_logger::init_from_env(env_logger::Env::new().default_filter_or("info"));

    // see https://github.com/actix/examples/blob/main/graphql/juniper-advanced/src/main.rs

    HttpServer::new(|| {
        App::new()
            .service(hello)
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}

 

