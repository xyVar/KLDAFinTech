#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>
#include <thread>
#include <chrono>
#include <libpq-fe.h>
#include "database/connection.h"
#include "../include/nlohmann/json.hpp"

using json = nlohmann::json;
using namespace klda;
using namespace std::chrono_literals;

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

// Build PostgreSQL connection string
std::string build_connection_string(const json& config) {
    std::string conn_str;

    const char* env_host = std::getenv("DATABASE_HOST");
    std::string host = env_host ? env_host : config["database"]["host"].get<std::string>();

    const char* env_port = std::getenv("DATABASE_PORT");
    int port = env_port ? std::stoi(env_port) : config["database"]["port"].get<int>();

    const char* env_name = std::getenv("DATABASE_NAME");
    std::string dbname = env_name ? env_name : config["database"]["name"].get<std::string>();

    const char* env_user = std::getenv("DATABASE_USER");
    std::string user = env_user ? env_user : config["database"]["user"].get<std::string>();

    const char* env_password = std::getenv("DATABASE_PASSWORD");
    std::string password = env_password ? env_password : config["database"]["password"].get<std::string>();

    conn_str += "host=" + host + " ";
    conn_str += "port=" + std::to_string(port) + " ";
    conn_str += "dbname=" + dbname + " ";
    conn_str += "user=" + user + " ";
    conn_str += "password=" + password;

    return conn_str;
}

// Fetch live ticks from CURRENT table
json fetch_live_ticks(database::Connection& db) {
    json ticks_array = json::array();

    PGresult* result = db.execute(
        "SELECT symbol, bid, ask, spread, volume, buy_volume, sell_volume, last_updated, "
        "EXTRACT(EPOCH FROM (NOW() - last_updated)) AS seconds_ago "
        "FROM current ORDER BY symbol;"
    );

    if (!result) {
        return ticks_array;
    }

    int rows = PQntuples(result);

    for (int i = 0; i < rows; i++) {
        json tick;
        tick["symbol"] = PQgetvalue(result, i, 0);
        tick["bid"] = std::stod(PQgetvalue(result, i, 1));
        tick["ask"] = std::stod(PQgetvalue(result, i, 2));
        tick["spread"] = std::stod(PQgetvalue(result, i, 3));
        tick["volume"] = std::stoll(PQgetvalue(result, i, 4));
        tick["buy_volume"] = std::stoll(PQgetvalue(result, i, 5));
        tick["sell_volume"] = std::stoll(PQgetvalue(result, i, 6));
        tick["last_updated"] = PQgetvalue(result, i, 7);
        tick["seconds_ago"] = std::stod(PQgetvalue(result, i, 8));

        ticks_array.push_back(tick);
    }

    PQclear(result);
    return ticks_array;
}

int main() {
    std::cout << "======================================" << std::endl;
    std::cout << "KLDA-HFT Live Tick Tracker" << std::endl;
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

    // Connect to database
    std::cout << "\n[2] Connecting to PostgreSQL..." << std::endl;
    database::Connection db(conn_str);

    if (!db.is_connected()) {
        std::cerr << "[ERROR] Failed to connect to database" << std::endl;
        return 1;
    }
    std::cout << "[OK] Connected to database" << std::endl;

    std::cout << "\n[3] Starting live tick tracking..." << std::endl;
    std::cout << "Writing to: /app/output/live_ticks.json" << std::endl;
    std::cout << "Press Ctrl+C to stop\n" << std::endl;

    int update_count = 0;

    // Continuous loop - update every second
    while (true) {
        // Fetch live ticks
        json ticks = fetch_live_ticks(db);

        // Create output JSON
        json output;
        output["timestamp"] = std::time(nullptr);
        output["update_count"] = ++update_count;
        output["total_assets"] = ticks.size();
        output["ticks"] = ticks;

        // Write to file (for HTML frontend to read)
        // Docker volume mount: /app/output -> Windows cpp-backend folder
        std::ofstream outfile("/app/output/live_ticks.json");
        outfile << output.dump(2);  // Pretty print with 2-space indent
        outfile.close();

        // Console output (every 10 updates)
        if (update_count % 10 == 0) {
            std::cout << "[" << update_count << "] Updated " << ticks.size() << " assets" << std::endl;
        }

        // Sleep 1 second
        std::this_thread::sleep_for(1s);
    }

    return 0;
}
