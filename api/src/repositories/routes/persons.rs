

use actix_web::{HttpResponse, Responder, get, http::Error, post, web};
use juniper::{Context, Variables, http::{GraphQLRequest, graphiql::graphiql_source}};
use log::info;

use crate::repositories::query::person_schema::{Ctx, Schema, create_schema}; 



#[post("/graphql")]
async fn persons(
    schema: web::Data<Schema>,
    data: web::Json<GraphQLRequest>,
) ->  Result<HttpResponse, Error> {
    // see https://github.com/actix/examples/blob/main/graphql/juniper-advanced/src/handlers.rs
    let ctx = ();
    let res = data.execute(&schema, &ctx).await;
    Ok(HttpResponse::Ok().json(res))
}


#[get("/graphiql")]
async fn graphql_playground() -> impl Responder {
    web::Html::new(graphiql_source("/graphql", None))
}

pub fn register(config: &mut web::ServiceConfig) {
    config
        .app_data(web::Data::new(create_schema()))
        .service(persons)
        .service(graphql_playground);
}