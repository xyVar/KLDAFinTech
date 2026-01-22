#ifndef KLDA_TRADING_ENGINE_H
#define KLDA_TRADING_ENGINE_H

#include <vector>
#include <map>
#include <string>
#include "../models/position.h"
#include "../database/connection.h"
#include "../../include/nlohmann/json.hpp"

using json = nlohmann::json;

namespace klda {
namespace trading {

class TradingEngine {
private:
    database::Connection& db;
    std::map<std::string, models::Position> open_positions;
    std::vector<models::Position> closed_positions;

    double account_balance;
    double initial_balance;
    int max_positions;
    double risk_per_trade;
    double target_profit_pct;
    double stop_loss_pct;

    // Renaissance thresholds
    double mean_rev_threshold;
    double spread_vol_threshold;
    double hmm_trend_threshold;
    double max_tx_cost;

public:
    TradingEngine(database::Connection& database, double initial_bal = 10000.0);

    // Position management
    bool open_position(const std::string& symbol, double bid, double ask, double spread);
    bool close_position(const std::string& symbol, double current_price, const std::string& reason);
    void check_exits(double current_price, const std::string& symbol);

    // Signal generation
    bool check_entry_signal(const std::string& symbol, double bid, const json& metrics);

    // Renaissance metrics calculation
    json calculate_mean_reversion(const std::string& symbol, double current_price);
    json calculate_spread_volatility(const std::string& symbol, double current_spread);
    json calculate_hmm_regime(const std::string& symbol);
    json calculate_transaction_cost(double spread);
    json calculate_kelly_size();

    // Position tracking
    void load_positions_from_database();
    void save_position_to_database(const models::Position& position);
    void update_position_in_database(const models::Position& position);

    // Statistics
    int get_open_position_count() const { return open_positions.size(); }
    double get_account_balance() const { return account_balance; }
    double get_realized_pnl() const;
    double get_unrealized_pnl(const std::map<std::string, double>& current_prices) const;
    double get_win_rate() const;

    // Export for dashboard
    json export_to_json(const std::map<std::string, double>& current_prices) const;
};

} // namespace trading
} // namespace klda

#endif // KLDA_TRADING_ENGINE_H
