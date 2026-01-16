#pragma once

#include <string>
#include <memory>
#include <libpq-fe.h>

namespace klda {
namespace database {

/**
 * PostgreSQL database connection wrapper
 * Uses libpq (PostgreSQL C library)
 */
class Connection {
public:
    Connection(const std::string& connection_string);
    ~Connection();

    // Disable copy (PostgreSQL connections can't be copied)
    Connection(const Connection&) = delete;
    Connection& operator=(const Connection&) = delete;

    // Check if connected
    bool is_connected() const;

    // Get connection status message
    std::string get_error() const;

    // Execute query and return result
    PGresult* execute(const std::string& query);

    // Get raw connection pointer (for advanced usage)
    PGconn* get_raw_connection() { return conn_; }

private:
    PGconn* conn_;
    std::string connection_string_;
};

} // namespace database
} // namespace klda
