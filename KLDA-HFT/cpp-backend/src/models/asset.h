#pragma once

#include <string>
#include "tick.h"

namespace klda {
namespace models {

/**
 * Asset structure
 * Represents an asset (stock, index, commodity) with its latest tick
 */
struct Asset {
    int symbol_id;
    std::string symbol;       // Database symbol (e.g., "TSLA")
    std::string mt5_symbol;   // MT5 broker symbol (e.g., "TSLA.US")
    Tick latest_tick;

    // Asset type enum
    enum class Type {
        STOCK,
        INDEX,
        COMMODITY,
        UNKNOWN
    };

    Type get_type() const {
        if (symbol == "VIX" || symbol == "NAS100") {
            return Type::INDEX;
        }
        else if (symbol == "NATGAS" || symbol == "SPOTCRUDE") {
            return Type::COMMODITY;
        }
        else {
            return Type::STOCK;
        }
    }

    std::string type_string() const {
        switch (get_type()) {
            case Type::STOCK:     return "STOCK";
            case Type::INDEX:     return "INDEX";
            case Type::COMMODITY: return "COMMODITY";
            default:              return "UNKNOWN";
        }
    }
};

} // namespace models
} // namespace klda
