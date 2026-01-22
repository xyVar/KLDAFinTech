#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>
#include <thread>
#include <chrono>
#include <algorithm>
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

// Calculate Mean Reversion (Simons) - Price distance from MA50
json calculate_mean_reversion(database::Connection& db, const std::string& symbol, double current_price) {
    std::string history_table = symbol;
    std::transform(history_table.begin(), history_table.end(), history_table.begin(), ::tolower);
    history_table += "_history";

    // Get last 50 ticks for MA50 calculation (OPTIMIZED from backtest)
    std::string query = "SELECT bid FROM " + history_table + " ORDER BY time DESC LIMIT 50;";
    PGresult* result = db.execute(query.c_str());

    json metrics;
    if (!result || PQntuples(result) < 50) {
        metrics["value"] = 0.0;
        metrics["signal"] = false;
        metrics["status"] = "INSUFFICIENT_DATA";
        if (result) PQclear(result);
        return metrics;
    }

    // Calculate MA50
    double sum = 0.0;
    for (int i = 0; i < 50; i++) {
        sum += std::stod(PQgetvalue(result, i, 0));
    }
    double ma50 = sum / 50.0;
    PQclear(result);

    // Calculate deviation percentage
    double deviation_pct = ((current_price - ma50) / ma50) * 100.0;

    metrics["value"] = deviation_pct;
    metrics["ma50"] = ma50;
    metrics["signal"] = (deviation_pct < -1.0);  // BUY signal when price is < -1% below MA
    metrics["status"] = (deviation_pct < -1.0) ? "BUY_ZONE" :
                       (deviation_pct > 1.0) ? "SELL_ZONE" : "NEUTRAL";

    return metrics;
}

// Calculate Order Flow Imbalance (Berlekamp) - Net buying vs selling
json calculate_order_flow(database::Connection& db, const std::string& symbol) {
    std::string history_table = symbol;
    std::transform(history_table.begin(), history_table.end(), history_table.begin(), ::tolower);
    history_table += "_history";

    // Get last 50 ticks for order flow calculation (OPTIMIZED from backtest)
    std::string query = "SELECT buy_volume, sell_volume FROM " + history_table +
                       " ORDER BY time DESC LIMIT 50;";
    PGresult* result = db.execute(query.c_str());

    json metrics;
    if (!result || PQntuples(result) < 50) {
        metrics["value"] = 0;
        metrics["signal"] = false;
        metrics["status"] = "INSUFFICIENT_DATA";
        if (result) PQclear(result);
        return metrics;
    }

    // Sum buy and sell volumes
    long long total_buy = 0;
    long long total_sell = 0;
    for (int i = 0; i < 50; i++) {
        total_buy += std::stoll(PQgetvalue(result, i, 0));
        total_sell += std::stoll(PQgetvalue(result, i, 1));
    }
    PQclear(result);

    long long net_flow = total_buy - total_sell;

    metrics["value"] = net_flow;
    metrics["buy_volume"] = total_buy;
    metrics["sell_volume"] = total_sell;
    metrics["signal"] = (net_flow > 2000);  // BUY signal when net buying > 2000
    metrics["status"] = (net_flow > 2000) ? "STRONG_BUY" :
                       (net_flow < -2000) ? "STRONG_SELL" : "NEUTRAL";

    return metrics;
}

// Calculate Spread Volatility (Patterson) - Spread widening detection
json calculate_spread_volatility(database::Connection& db, const std::string& symbol, double current_spread) {
    std::string history_table = symbol;
    std::transform(history_table.begin(), history_table.end(), history_table.begin(), ::tolower);
    history_table += "_history";

    // Get last 100 ticks for average spread calculation
    std::string query = "SELECT spread FROM " + history_table + " ORDER BY time DESC LIMIT 100;";
    PGresult* result = db.execute(query.c_str());

    json metrics;
    if (!result || PQntuples(result) < 100) {
        metrics["value"] = 0.0;
        metrics["signal"] = false;
        metrics["status"] = "INSUFFICIENT_DATA";
        if (result) PQclear(result);
        return metrics;
    }

    // Calculate average spread
    double sum = 0.0;
    for (int i = 0; i < 100; i++) {
        sum += std::stod(PQgetvalue(result, i, 0));
    }
    double avg_spread = sum / 100.0;
    PQclear(result);

    // Calculate spread volatility percentage
    double spread_vol_pct = ((current_spread - avg_spread) / avg_spread) * 100.0;

    metrics["value"] = spread_vol_pct;
    metrics["avg_spread"] = avg_spread;
    metrics["signal"] = (spread_vol_pct > 20.0);  // Signal when spread widens > 20%
    metrics["status"] = (spread_vol_pct > 20.0) ? "WIDENING" :
                       (spread_vol_pct < -20.0) ? "TIGHTENING" : "NORMAL";

    return metrics;
}

// Calculate HMM Regime (Brown) - Simplified trend detection
json calculate_hmm_regime(database::Connection& db, const std::string& symbol) {
    std::string history_table = symbol;
    std::transform(history_table.begin(), history_table.end(), history_table.begin(), ::tolower);
    history_table += "_history";

    // Get last 200 ticks for trend analysis (OPTIMIZED from backtest)
    std::string query = "SELECT bid FROM " + history_table + " ORDER BY time DESC LIMIT 200;";
    PGresult* result = db.execute(query.c_str());

    json metrics;
    if (!result || PQntuples(result) < 200) {
        metrics["value"] = "UNKNOWN";
        metrics["signal"] = false;
        metrics["status"] = "INSUFFICIENT_DATA";
        if (result) PQclear(result);
        return metrics;
    }

    // Simple trend detection: compare first 100 vs last 100 ticks
    double recent_avg = 0.0;  // Most recent 100 ticks
    double older_avg = 0.0;   // Previous 100 ticks

    for (int i = 0; i < 100; i++) {
        recent_avg += std::stod(PQgetvalue(result, i, 0));
    }
    for (int i = 100; i < 200; i++) {
        older_avg += std::stod(PQgetvalue(result, i, 0));
    }
    recent_avg /= 100.0;
    older_avg /= 100.0;
    PQclear(result);

    double trend_pct = ((recent_avg - older_avg) / older_avg) * 100.0;

    std::string regime;
    if (trend_pct > 0.5) {
        regime = "BULLISH";
    } else if (trend_pct < -0.5) {
        regime = "BEARISH";
    } else {
        regime = "NEUTRAL";
    }

    metrics["value"] = regime;
    metrics["trend_pct"] = trend_pct;
    metrics["signal"] = (regime == "BULLISH");  // BUY signal only in BULLISH regime
    metrics["status"] = regime;

    return metrics;
}

// Calculate Transaction Cost (Mercer) - "The Devil"
json calculate_transaction_cost(double spread, double price) {
    json metrics;

    // Half spread as transaction cost (typical CFD execution cost)
    double spread_cost = spread / 2.0;

    // Daily swap cost (€1000 account, €500 position, -7% annual = -0.096 EUR/day)
    double daily_swap = 0.096;  // Fixed for now, should be position-size dependent

    // Total cost per trade
    double total_cost = spread_cost + daily_swap;

    metrics["value"] = total_cost;
    metrics["spread_cost"] = spread_cost;
    metrics["swap_cost"] = daily_swap;
    metrics["signal"] = (total_cost < 10.0);  // Signal when cost < €10
    metrics["status"] = (total_cost < 10.0) ? "ACCEPTABLE" : "HIGH_COST";

    return metrics;
}

// Calculate Kelly Position Size
json calculate_kelly_size(double account_balance = 1000.0) {
    json metrics;

    // Renaissance Medallion: Win rate 50.75%, expected value 0.75% per trade
    double win_rate = 0.5075;
    double avg_win = 15.0;  // €15 average win
    double avg_loss = 14.25;  // €14.25 average loss

    // Kelly formula: f = (p*b - q) / b
    // where p = win prob, q = loss prob, b = win/loss ratio
    double p = win_rate;
    double q = 1.0 - win_rate;
    double b = avg_win / avg_loss;

    double kelly_fraction = (p * b - q) / b;

    // Conservative Kelly (half Kelly for safety)
    double kelly_pct = (kelly_fraction / 2.0) * 100.0;
    double position_size = account_balance * (kelly_pct / 100.0);

    // Cap at 2% risk per trade
    if (kelly_pct > 2.0) {
        kelly_pct = 2.0;
        position_size = account_balance * 0.02;
    }

    metrics["value"] = position_size;
    metrics["kelly_pct"] = kelly_pct;
    metrics["signal"] = (kelly_pct < 2.0);  // Safe if < 2%
    metrics["status"] = (kelly_pct < 2.0) ? "SAFE" : "HIGH_RISK";

    return metrics;
}

// Fetch live ticks with Renaissance metrics
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
        std::string symbol = PQgetvalue(result, i, 0);
        double bid = std::stod(PQgetvalue(result, i, 1));
        double ask = std::stod(PQgetvalue(result, i, 2));
        double spread = std::stod(PQgetvalue(result, i, 3));

        tick["symbol"] = symbol;
        tick["bid"] = bid;
        tick["ask"] = ask;
        tick["spread"] = spread;
        tick["volume"] = std::stoll(PQgetvalue(result, i, 4));
        tick["buy_volume"] = std::stoll(PQgetvalue(result, i, 5));
        tick["sell_volume"] = std::stoll(PQgetvalue(result, i, 6));
        tick["last_updated"] = PQgetvalue(result, i, 7);
        tick["seconds_ago"] = std::stod(PQgetvalue(result, i, 8));

        // Calculate Renaissance metrics
        double current_price = (bid + ask) / 2.0;  // Mid price

        tick["renaissance"] = {
            {"mean_reversion", calculate_mean_reversion(db, symbol, current_price)},
            {"order_flow", calculate_order_flow(db, symbol)},
            {"spread_volatility", calculate_spread_volatility(db, symbol, spread)},
            {"hmm_regime", calculate_hmm_regime(db, symbol)},
            {"transaction_cost", calculate_transaction_cost(spread, current_price)},
            {"kelly_size", calculate_kelly_size()}
        };

        // Overall signal - ALL conditions must be TRUE
        bool all_conditions =
            tick["renaissance"]["mean_reversion"]["signal"].get<bool>() &&
            tick["renaissance"]["order_flow"]["signal"].get<bool>() &&
            tick["renaissance"]["spread_volatility"]["signal"].get<bool>() &&
            tick["renaissance"]["hmm_regime"]["signal"].get<bool>() &&
            tick["renaissance"]["transaction_cost"]["signal"].get<bool>() &&
            tick["renaissance"]["kelly_size"]["signal"].get<bool>();

        tick["renaissance"]["overall_signal"] = all_conditions ? "ENTER_LONG" : "WAIT";

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
