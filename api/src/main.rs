


mod repositories;
mod interfaces;
mod entities;


use actix_web::{App, HttpServer};
use actix_cors::Cors;
use actix_web::{middleware::Logger};
use log::{debug, error, log_enabled, info, Level};


use crate::repositories::routes::persons::register;




#[actix_web::main]
async fn main() -> std::io::Result<()> {

    dotenv::dotenv().ok();
    env_logger::init_from_env(env_logger::Env::new().default_filter_or("info"));

    // see https://github.com/actix/examples/blob/main/graphql/juniper-advanced/src/main.rs

    info!("starting HTTP server on port 8080");
    info!("GraphiQL playground: http://localhost:8080/graphiql");

    HttpServer::new(move || {
        App::new()
            //.app_data(Data::new())
            .configure(register)
            .wrap(Cors::permissive())
            .wrap(Logger::default())
    })
    .workers(2)
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}

 

