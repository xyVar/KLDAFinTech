#pragma once

#include <string>
#include <chrono>
#include <cstdint>

namespace klda {
namespace models {

/**
 * Bar data structure (OHLCV)
 * Represents historical bar data for backtesting
 */
struct Bar {
    std::chrono::system_clock::time_point time;
    std::string symbol;
    std::string timeframe;  // "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"
    double open;
    double high;
    double low;
    double close;
    int64_t volume;
    int spread;

    // Helper methods
    double body() const {
        return std::abs(close - open);
    }

    double range() const {
        return high - low;
    }

    bool is_bullish() const {
        return close > open;
    }

    bool is_bearish() const {
        return close < open;
    }

    double upper_wick() const {
        return high - std::max(open, close);
    }

    double lower_wick() const {
        return std::min(open, close) - low;
    }
};

} // namespace models
} // namespace klda
