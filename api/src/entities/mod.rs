use std::fmt;



pub struct StorableEntity {
    pub uid: String,
    pub title: String,
    pub permalink: String,
}

pub struct Biography {
    root: StorableEntity,
    full_name: Option<String>
}

pub struct Movie {
    root: StorableEntity,
}


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
        write!(f, "<{}: {}>", self.root.uid, self.root.title)
    }
}