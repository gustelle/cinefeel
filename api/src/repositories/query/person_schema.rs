use juniper::{EmptyMutation, EmptySubscription, FieldResult, GraphQLObject, RootNode};

use crate::{interfaces::db::DbRepository};
use crate::repositories::db::person_repository::PersonRepository;

pub struct QueryRoot;

// Arbitrary context data.
pub struct PersonContext {
    pub repo: PersonRepository,
}

use serde::{Deserialize, Serialize};

impl juniper::Context for PersonContext {
    
}

// There is also a custom derive for mapping GraphQL input objects.
#[derive(GraphQLObject)]
#[derive(Serialize, Deserialize)]
struct QueryResult {
    title: String,
    uid: String,
    permalink: String,
    birth_date: Option<String>,
    full_name: Option<String>,
}

#[juniper::graphql_object]
impl QueryRoot {
    fn members<'a>(uid: String, context: &'a PersonContext) -> FieldResult<Vec<QueryResult>> {
        let repo = &context.repo;
        let mut params = std::collections::HashMap::new();
        params.insert("uid".to_string(), uid);
        match repo.query("MATCH (n: Person {uid: $uid}) RETURN n;", params) {
            Some(records) => {
                Ok(records.into_iter().map(|p| QueryResult { 
                    title: p.root.title,
                    uid: p.root.uid,
                    permalink: p.root.permalink,
                    birth_date: p.biography.as_ref().and_then(|b| b.birth_date.clone()),
                    full_name: p.biography.as_ref().and_then(|b| b.full_name.clone()),

                }).collect())
            }   ,
            None => Ok(vec![]),
        }
    }
}



pub type Schema = RootNode<QueryRoot, EmptyMutation<PersonContext>, EmptySubscription<PersonContext>>;

pub fn create_schema() -> Schema {
    Schema::new(QueryRoot {}, EmptyMutation::new(), EmptySubscription::new())
}