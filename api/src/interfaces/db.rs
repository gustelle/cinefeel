use std::collections::HashMap;


pub trait DbRepository<T> {
    fn new() -> Self;
    fn query(&self, query: &str, params: HashMap<String, String>) -> Option<Vec<T>>;
}