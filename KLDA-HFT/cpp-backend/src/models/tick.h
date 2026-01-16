#pragma once

#include <string>
#include <chrono>
#include <cstdint>

namespace klda {
namespace models {

/**
 * Tick data structure
 * Represents a single tick from MT5 broker
 */
struct Tick {
    std::chrono::system_clock::time_point time;
    std::string symbol;
    double bid;
    double ask;
    double spread;
    int64_t volume;
    int64_t buy_volume;
    int64_t sell_volume;
    int flags;

    // MT5 Tick Flags
    static constexpr int FLAG_BID    = 2;   // Bid price changed
    static constexpr int FLAG_ASK    = 4;   // Ask price changed
    static constexpr int FLAG_LAST   = 8;   // Last trade price
    static constexpr int FLAG_VOLUME = 16;  // Volume available
    static constexpr int FLAG_BUY    = 32;  // Buyer initiated trade
    static constexpr int FLAG_SELL   = 64;  // Seller initiated trade

    // Helper methods
    bool is_quote() const {
        return (flags & FLAG_LAST) == 0;
    }

    bool is_trade() const {
        return (flags & FLAG_LAST) != 0;
    }

    bool is_buy_trade() const {
        return (flags & FLAG_BUY) != 0;
    }

    bool is_sell_trade() const {
        return (flags & FLAG_SELL) != 0;
    }

    // Get spread in dollars
    double spread_dollars() const {
        return ask - bid;
    }
};

} // namespace models
} // namespace klda
