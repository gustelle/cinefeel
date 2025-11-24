use std::env;

use rsmgclient::{ConnectionStatus, Connection, ConnectParams, SSLMode};



pub fn get_connection() -> Option<Connection> {
    let host = env::var("GRAPHDB_HOST").unwrap_or("localhost".to_string());
    let db_port: String = env::var("GRAPHDB_PORT").unwrap_or("7687".to_string());
    let db_port: u16 = db_port.parse().unwrap_or(7687);

    // Connect to Memgraph 
    let connect_params = ConnectParams {
        host: Some(host),
        port: db_port,
        sslmode: SSLMode::Disable,
        ..Default::default()
    };
    let connection = Connection::connect(&connect_params).unwrap();

    // Check if connection is established.
    let status = connection.status();
    
    if status != ConnectionStatus::Ready {
        println!("Connection failed with status: {:?}", status);
        return None;
        
    } else {
        println!("Connection established with status: {:?}", status);
    }

    Some(connection)

}