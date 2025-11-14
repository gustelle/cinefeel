

pub trait DbRepository {
    fn connect(&self) -> bool;
    fn disconnect(&self) -> bool;
    fn query(&self, query: &str, params: Option<&[(&str, &str)]>) -> Option<Vec<String>>;
}