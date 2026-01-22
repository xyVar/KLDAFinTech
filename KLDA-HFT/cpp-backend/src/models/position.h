#ifndef KLDA_POSITION_H
#define KLDA_POSITION_H

#include <string>
#include <chrono>

namespace klda {
namespace models {

struct Position {
    int id;
    std::string symbol;
    std::chrono::system_clock::time_point entry_time;
    double entry_price;
    double shares;
    double position_size;
    double stop_loss;
    double take_profit;
    std::string status;  // "OPEN" or "CLOSED"
    std::chrono::system_clock::time_point exit_time;
    double exit_price;
    double pnl;

    // Constructor for new position
    Position(const std::string& sym, double entry, double shrs, double size, double sl, double tp)
        : symbol(sym), entry_price(entry), shares(shrs), position_size(size),
          stop_loss(sl), take_profit(tp), status("OPEN"),
          exit_price(0.0), pnl(0.0) {
        entry_time = std::chrono::system_clock::now();
    }

    // Calculate current P&L
    double calculate_pnl(double current_price) const {
        return (current_price - entry_price) * shares;
    }

    // Calculate P&L percentage
    double calculate_pnl_pct(double current_price) const {
        return ((current_price - entry_price) / entry_price) * 100.0;
    }

    // Check if stop loss hit
    bool is_stop_loss_hit(double current_price) const {
        return current_price <= stop_loss;
    }

    // Check if take profit hit
    bool is_take_profit_hit(double current_price) const {
        return current_price >= take_profit;
    }
};

} // namespace models
} // namespace klda

#endif // KLDA_POSITION_H
