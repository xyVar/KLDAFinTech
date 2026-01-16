#include "connection.h"
#include <iostream>

namespace klda {
namespace database {

Connection::Connection(const std::string& connection_string)
    : connection_string_(connection_string), conn_(nullptr) {

    // Connect to database
    conn_ = PQconnectdb(connection_string.c_str());

    // Check connection status
    if (PQstatus(conn_) != CONNECTION_OK) {
        std::cerr << "[ERROR] Database connection failed: " << PQerrorMessage(conn_) << std::endl;
        PQfinish(conn_);
        conn_ = nullptr;
    } else {
        std::cout << "[OK] Connected to PostgreSQL database" << std::endl;
    }
}

Connection::~Connection() {
    if (conn_) {
        PQfinish(conn_);
        std::cout << "[OK] Database connection closed" << std::endl;
    }
}

bool Connection::is_connected() const {
    return conn_ != nullptr && PQstatus(conn_) == CONNECTION_OK;
}

std::string Connection::get_error() const {
    if (conn_) {
        return std::string(PQerrorMessage(conn_));
    }
    return "No connection";
}

PGresult* Connection::execute(const std::string& query) {
    if (!is_connected()) {
        std::cerr << "[ERROR] Cannot execute query: not connected" << std::endl;
        return nullptr;
    }

    PGresult* result = PQexec(conn_, query.c_str());

    // Check result status
    ExecStatusType status = PQresultStatus(result);
    if (status != PGRES_TUPLES_OK && status != PGRES_COMMAND_OK) {
        std::cerr << "[ERROR] Query failed: " << PQerrorMessage(conn_) << std::endl;
        PQclear(result);
        return nullptr;
    }

    return result;
}

} // namespace database
} // namespace klda
