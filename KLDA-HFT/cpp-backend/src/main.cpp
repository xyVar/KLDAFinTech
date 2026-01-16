#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>
#include <libpq-fe.h>
#include "database/connection.h"
#include "../include/nlohmann/json.hpp"

using json = nlohmann::json;
using namespace klda;

// Load configuration from config.json
json load_config(const std::string& config_path) {
    std::ifstream file(config_path);
    if (!file.is_open()) {
        std::cerr << "[ERROR] Could not open config.json" << std::endl;
        return json();
    }

    json config;
    file >> config;
    return config;
}

// Build PostgreSQL connection string from config and environment variables
// Environment variables override config.json values
std::string build_connection_string(const json& config) {
    std::string conn_str;

    // Get host (env var overrides config)
    const char* env_host = std::getenv("DATABASE_HOST");
    std::string host = env_host ? env_host : config["database"]["host"].get<std::string>();

    // Get port (env var overrides config)
    const char* env_port = std::getenv("DATABASE_PORT");
    int port = env_port ? std::stoi(env_port) : config["database"]["port"].get<int>();

    // Get database name (env var overrides config)
    const char* env_name = std::getenv("DATABASE_NAME");
    std::string dbname = env_name ? env_name : config["database"]["name"].get<std::string>();

    // Get user (env var overrides config)
    const char* env_user = std::getenv("DATABASE_USER");
    std::string user = env_user ? env_user : config["database"]["user"].get<std::string>();

    // Get password (env var overrides config)
    const char* env_password = std::getenv("DATABASE_PASSWORD");
    std::string password = env_password ? env_password : config["database"]["password"].get<std::string>();

    // Build connection string
    conn_str += "host=" + host + " ";
    conn_str += "port=" + std::to_string(port) + " ";
    conn_str += "dbname=" + dbname + " ";
    conn_str += "user=" + user + " ";
    conn_str += "password=" + password;

    return conn_str;
}

int main() {
    std::cout << "======================================" << std::endl;
    std::cout << "KLDA-HFT C++ Backend Engine" << std::endl;
    std::cout << "======================================" << std::endl;

    // Load configuration
    std::cout << "\n[1] Loading configuration..." << std::endl;
    json config = load_config("config.json");
    if (config.empty()) {
        std::cerr << "[ERROR] Failed to load config.json" << std::endl;
        return 1;
    }
    std::cout << "[OK] Configuration loaded" << std::endl;

    // Build connection string
    std::string conn_str = build_connection_string(config);
    std::cout << "[OK] Connection string built" << std::endl;

    // Connect to database
    std::cout << "\n[2] Connecting to PostgreSQL..." << std::endl;
    database::Connection db(conn_str);

    if (!db.is_connected()) {
        std::cerr << "[ERROR] Failed to connect to database" << std::endl;
        return 1;
    }

    // Test query: Get all assets from CURRENT table
    std::cout << "\n[3] Querying CURRENT table..." << std::endl;
    PGresult* result = db.execute("SELECT symbol, bid, ask, last_updated FROM current ORDER BY symbol;");

    if (!result) {
        std::cerr << "[ERROR] Query failed" << std::endl;
        return 1;
    }

    // Display results
    int rows = PQntuples(result);
    std::cout << "[OK] Found " << rows << " assets\n" << std::endl;

    std::cout << "Symbol     | Bid       | Ask       | Last Updated" << std::endl;
    std::cout << "-------------------------------------------------------------" << std::endl;

    for (int i = 0; i < rows; i++) {
        std::string symbol = PQgetvalue(result, i, 0);
        std::string bid = PQgetvalue(result, i, 1);
        std::string ask = PQgetvalue(result, i, 2);
        std::string updated = PQgetvalue(result, i, 3);

        // Format output
        printf("%-10s | %9s | %9s | %s\n",
               symbol.c_str(), bid.c_str(), ask.c_str(), updated.substr(0, 19).c_str());
    }

    // Cleanup
    PQclear(result);

    std::cout << "\n======================================" << std::endl;
    std::cout << "[SUCCESS] Database connection test passed!" << std::endl;
    std::cout << "======================================" << std::endl;

    return 0;
}
