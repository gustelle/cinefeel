use std::fmt;
use crate::entities::storable::StorableEntity;

pub struct Movie {
    root: StorableEntity,
}

impl fmt::Display for Movie {
    // This trait requires `fmt` with this exact signature.
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        // Write strictly the first element into the supplied output
        // stream: `f`. Returns `fmt::Result` which indicates whether the
        // operation succeeded or failed. Note that `write!` uses syntax which
        // is very similar to `println!`.
        write!(f, "<{}: {}>", self.root.uid, self.root.title)
    }
}

