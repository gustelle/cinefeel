use std::fmt;

use crate::entities::storable::StorableEntity;

#[derive(Debug)]
pub struct Biography {
    pub(crate) full_name: Option<String>,
    pub(crate) birth_date: Option<String>,
}

#[derive(Debug)]
pub struct Person {
    pub(crate) root: StorableEntity,
    pub(crate) biography: Option<Biography>,
}

impl fmt::Display for Person {
    // This trait requires `fmt` with this exact signature.
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        // Write strictly the first element into the supplied output
        // stream: `f`. Returns `fmt::Result` which indicates whether the
        // operation succeeded or failed. Note that `write!` uses syntax which
        // is very similar to `println!`.
        write!(f, "<{}: {} | {}>", self.root.uid, self.root.title, self.biography.as_ref().map_or("".to_string(), |b| format!("{}", b)))
    }
}

impl fmt::Display for Biography {
    // This trait requires `fmt` with this exact signature.
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        // Write strictly the first element into the supplied output
        // stream: `f`. Returns `fmt::Result` which indicates whether the
        // operation succeeded or failed. Note that `write!` uses syntax which
        // is very similar to `println!`.
        write!(f, "full_name: {:?}", self.full_name)
    }
}