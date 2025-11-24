

use actix_web::{HttpResponse, Responder, get, http::Error, post, web};
use juniper::{http::{GraphQLRequest, graphiql::graphiql_source}};
use log::info;

use crate::interfaces::db::DbRepository;
use crate::repositories::db::person_repository::PersonRepository;
use crate::repositories::query::person_schema::{Schema, create_schema, PersonContext}; 



#[post("/graphql")]
async fn persons(
    schema: web::Data<Schema>,
    data: web::Json<GraphQLRequest>,
    ctx: web::Data<PersonContext>,
) ->  Result<HttpResponse, Error> {
    
    let res = data.execute(&schema, &ctx).await;
    Ok(HttpResponse::Ok().json(res))
}


#[get("/graphiql")]
async fn graphql_playground() -> impl Responder {
    web::Html::new(graphiql_source("/graphql", None))
}

pub fn register_persons_routes(config: &mut web::ServiceConfig) {

    let ctx = PersonContext {
        repo: PersonRepository::new(),
    };

    config
        .app_data(web::Data::new(create_schema()))
        .app_data(web::Data::new(ctx))
        .service(persons)
        .service(graphql_playground);
}