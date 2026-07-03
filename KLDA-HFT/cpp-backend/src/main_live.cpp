/**
 * KLDA-HFT Renaissance Reasoning Engine
 *
 * Reads live ticks from PostgreSQL universal ticks table.
 * Calculates 5 Renaissance metrics per symbol.
 * Generates BUY signals when all conditions align.
 * Writes signals to signals table.
 * Outputs live_ticks.json for dashboard every second.
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <cmath>
#include <ctime>
#include <cstdlib>
#include <thread>
#include <chrono>
#include <algorithm>
#include <stdexcept>
#include <libpq-fe.h>
#include "database/connection.h"
#include "../include/nlohmann/json.hpp"

using json = nlohmann::json;
using namespace klda;
using namespace std::chrono_literals;

// ============================================================
// RENAISSANCE THRESHOLDS
// ============================================================
const double MEAN_REV_THRESHOLD   = -1.0;
const double SPREAD_VOL_THRESHOLD = 20.0;
const double HMM_TREND_THRESHOLD  = 0.1;
const double MAX_TX_COST          = 10.0;
const double KELLY_WIN_RATE       = 0.5075;
const double KELLY_MAX_PCT        = 2.0;

// ============================================================
// SAFE HELPERS — prevent stod / NaN / Inf crashes
// ============================================================

// Safe string-to-double: returns 0.0 if string is empty or invalid
double safe_stod(const char* s) {
    if (!s || s[0] == '\0') return 0.0;
    try { return std::stod(s); }
    catch (...) { return 0.0; }
}

// Sanitise a double: replace NaN or Inf with fallback (default 0)
double safe_d(double v, double fallback = 0.0) {
    if (std::isnan(v) || std::isinf(v)) return fallback;
    return v;
}

// ============================================================
// LOAD CONFIG
// ============================================================
json load_config(const std::string& path) {
    try {
        std::ifstream f(path);
        if (!f.is_open()) return json();
        json cfg; f >> cfg;
        return cfg;
    } catch (...) { return json(); }
}

std::string build_conn_str(const json& cfg) {
    auto& db = cfg["database"];
    return "host=" + db["host"].get<std::string>() +
           " port=" + std::to_string(db["port"].get<int>()) +
           " dbname=" + db["name"].get<std::string>() +
           " user=" + db["user"].get<std::string>() +
           " password=" + db["password"].get<std::string>();
}

// ============================================================
// METRIC 1: MEAN REVERSION
// ============================================================
struct MeanRevResult {
    double deviation_pct = 0.0;
    double ma50          = 0.0;
    bool   signal        = false;
    std::string status   = "NO_DATA";
};

MeanRevResult calc_mean_reversion(database::Connection& db,
                                   const std::string& symbol,
                                   double current_price) {
    MeanRevResult r;
    try {
        std::string q = "SELECT bid FROM ticks WHERE symbol = '" + symbol +
                        "' ORDER BY time DESC LIMIT 50";
        PGresult* res = db.execute(q);
        if (!res || PQntuples(res) < 20) {
            if (res) PQclear(res);
            return r;
        }
        int n = PQntuples(res);
        double sum = 0.0;
        for (int i = 0; i < n; i++)
            sum += safe_stod(PQgetvalue(res, i, 0));
        PQclear(res);

        r.ma50 = (n > 0) ? sum / n : 0.0;
        if (r.ma50 > 0.0)
            r.deviation_pct = ((current_price - r.ma50) / r.ma50) * 100.0;
        r.deviation_pct = safe_d(r.deviation_pct);
        r.signal  = (r.deviation_pct < MEAN_REV_THRESHOLD);
        r.status  = r.signal ? "BUY_ZONE" :
                   (r.deviation_pct > 1.0) ? "SELL_ZONE" : "NEUTRAL";
    } catch (...) {}
    return r;
}

// ============================================================
// METRIC 2: SPREAD VOLATILITY
// ============================================================
struct SpreadVolResult {
    double spread_vol_pct = 0.0;
    double avg_spread     = 0.0;
    bool   signal         = true;   // true = spread NORMAL
    std::string status    = "NO_DATA";
};

SpreadVolResult calc_spread_vol(database::Connection& db,
                                 const std::string& symbol,
                                 double current_spread) {
    SpreadVolResult r;
    try {
        std::string q = "SELECT spread FROM ticks WHERE symbol = '" + symbol +
                        "' ORDER BY time DESC LIMIT 100";
        PGresult* res = db.execute(q);
        if (!res || PQntuples(res) < 20) {
            if (res) PQclear(res);
            r.signal = true;
            return r;
        }
        int n = PQntuples(res);
        double sum = 0.0;
        for (int i = 0; i < n; i++)
            sum += safe_stod(PQgetvalue(res, i, 0));
        PQclear(res);

        r.avg_spread = (n > 0) ? sum / n : 0.0;
        if (r.avg_spread > 0.0)
            r.spread_vol_pct = ((current_spread - r.avg_spread) / r.avg_spread) * 100.0;
        r.spread_vol_pct = safe_d(r.spread_vol_pct);
        r.signal  = (r.spread_vol_pct <= SPREAD_VOL_THRESHOLD);
        r.status  = r.signal ? "NORMAL" : "WIDENING";
    } catch (...) { r.signal = true; }
    return r;
}

// ============================================================
// METRIC 3: HMM REGIME
// ============================================================
struct RegimeResult {
    std::string regime  = "UNKNOWN";
    double trend_pct    = 0.0;
    bool   signal       = true;
    std::string status  = "NO_DATA";
};

RegimeResult calc_regime(database::Connection& db, const std::string& symbol) {
    RegimeResult r;
    try {
        std::string q = "SELECT bid FROM ticks WHERE symbol = '" + symbol +
                        "' ORDER BY time DESC LIMIT 200";
        PGresult* res = db.execute(q);
        if (!res || PQntuples(res) < 40) {
            if (res) PQclear(res);
            r.signal = true;
            r.status = "INSUFFICIENT";
            return r;
        }
        int n    = PQntuples(res);
        int half = n / 2;
        double recent = 0.0, older = 0.0;
        for (int i = 0;    i < half; i++) recent += safe_stod(PQgetvalue(res, i, 0));
        for (int i = half; i < n;    i++) older  += safe_stod(PQgetvalue(res, i, 0));
        PQclear(res);

        recent /= (half > 0 ? half : 1);
        older  /= (n - half > 0 ? n - half : 1);

        if (older > 0.0)
            r.trend_pct = ((recent - older) / older) * 100.0;
        r.trend_pct = safe_d(r.trend_pct);

        if      (r.trend_pct >  HMM_TREND_THRESHOLD) r.regime = "BULLISH";
        else if (r.trend_pct < -HMM_TREND_THRESHOLD) r.regime = "BEARISH";
        else                                          r.regime = "NEUTRAL";

        r.signal = (r.regime == "BULLISH" || r.regime == "NEUTRAL");
        r.status = r.regime;
    } catch (...) { r.signal = true; }
    return r;
}

// ============================================================
// METRIC 4: TRANSACTION COST
// ============================================================
struct CostResult {
    double total_cost  = 0.0;
    bool   signal      = false;
    std::string status = "NO_DATA";
};

CostResult calc_tx_cost(double spread, double price) {
    CostResult r;
    double spread_cost = spread / 2.0;
    double swap_daily  = price * 0.000619 / 365.0;
    r.total_cost = safe_d(spread_cost + swap_daily);
    r.signal     = (r.total_cost < MAX_TX_COST);
    r.status     = r.signal ? "ACCEPTABLE" : "HIGH_COST";
    return r;
}

// ============================================================
// METRIC 5: KELLY POSITION SIZE
// ============================================================
struct KellyResult {
    double kelly_pct     = 0.0;
    double position_size = 0.0;
    bool   signal        = false;
    std::string status   = "NO_DATA";
};

KellyResult calc_kelly(double account_balance) {
    KellyResult r;
    double p = KELLY_WIN_RATE;
    double q = 1.0 - p;
    double b = 1.5;
    double f = (p * b - q) / b;
    r.kelly_pct     = safe_d(std::min(f * 50.0, KELLY_MAX_PCT));
    r.position_size = safe_d(account_balance * (r.kelly_pct / 100.0));
    r.signal  = (r.kelly_pct > 0 && r.kelly_pct <= KELLY_MAX_PCT);
    r.status  = r.signal ? "SAFE" : "HIGH_RISK";
    return r;
}

// ============================================================
// WRITE SIGNAL TO DB
// ============================================================
void write_signal(database::Connection& db,
                  const std::string& symbol,
                  const std::string& action,
                  double price,
                  double confidence,
                  const MeanRevResult& mr,
                  const RegimeResult& reg,
                  const SpreadVolResult& sv,
                  const CostResult& cost,
                  const KellyResult& kelly) {
    try {
        std::ostringstream q;
        q << "INSERT INTO signals (symbol, action, price, confidence, "
          << "mean_rev, regime, spread_ok, cost_ok, kelly_pct, status) VALUES ("
          << "'" << symbol << "',"
          << "'" << action << "',"
          << safe_d(price) << ","
          << safe_d(confidence) << ","
          << safe_d(mr.deviation_pct) << ","
          << "'" << reg.regime << "',"
          << (sv.signal ? "true" : "false") << ","
          << (cost.signal ? "true" : "false") << ","
          << safe_d(kelly.kelly_pct) << ","
          << "'PENDING')";
        PGresult* res = db.execute(q.str());
        if (res) PQclear(res);
    } catch (...) {}
}

// ============================================================
// PROCESS ONE SYMBOL
// ============================================================
json process_symbol(database::Connection& db,
                    const std::string& symbol,
                    double bid, double ask, double spread,
                    double seconds_ago,
                    double account_balance) {
    json out;
    try {
        out["symbol"]      = symbol;
        out["bid"]         = safe_d(bid);
        out["ask"]         = safe_d(ask);
        out["spread"]      = safe_d(spread);
        out["seconds_ago"] = safe_d(seconds_ago);

        double price = safe_d((bid + ask) / 2.0);

        auto mr    = calc_mean_reversion(db, symbol, price);
        auto sv    = calc_spread_vol(db, symbol, spread);
        auto reg   = calc_regime(db, symbol);
        auto cost  = calc_tx_cost(spread, price);
        auto kelly = calc_kelly(account_balance);

        int conditions_met = 0;
        if (mr.signal)    conditions_met++;
        if (sv.signal)    conditions_met++;
        if (reg.signal)   conditions_met++;
        if (cost.signal)  conditions_met++;
        if (kelly.signal) conditions_met++;

        double confidence = (conditions_met / 5.0) * 100.0;
        bool   enter      = (conditions_met == 5);
        std::string overall = enter ? "ENTER_LONG" : "WAIT";

        out["price"]      = price;
        out["confidence"] = confidence;
        out["signal"]     = overall;

        out["metrics"] = {
            {"mean_reversion",    {{"value",  safe_d(mr.deviation_pct)},  {"ma50", safe_d(mr.ma50)},          {"signal", mr.signal}, {"status", mr.status}}},
            {"spread_volatility", {{"value",  safe_d(sv.spread_vol_pct)}, {"avg_spread", safe_d(sv.avg_spread)}, {"signal", sv.signal}, {"status", sv.status}}},
            {"regime",            {{"value",  reg.regime},                {"trend_pct", safe_d(reg.trend_pct)},  {"signal", reg.signal}, {"status", reg.status}}},
            {"transaction_cost",  {{"value",  safe_d(cost.total_cost)},   {"signal", cost.signal},  {"status", cost.status}}},
            {"kelly",             {{"pct",    safe_d(kelly.kelly_pct)},   {"size", safe_d(kelly.position_size)}, {"signal", kelly.signal}, {"status", kelly.status}}}
        };

        if (enter) {
            write_signal(db, symbol, "BUY", price, confidence, mr, reg, sv, cost, kelly);
            std::cout << "[SIGNAL] BUY " << symbol << " @ " << price
                      << " confidence=" << confidence << "%" << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "[WARN] process_symbol(" << symbol << "): " << e.what() << std::endl;
        out["signal"] = "WAIT";
        out["confidence"] = 0.0;
    } catch (...) {
        std::cerr << "[WARN] process_symbol(" << symbol << "): unknown error" << std::endl;
        out["signal"] = "WAIT";
        out["confidence"] = 0.0;
    }
    return out;
}

// ============================================================
// MAIN LOOP
// ============================================================
int main() {
    std::cout << "============================================" << std::endl;
    std::cout << "KLDA-HFT Renaissance Reasoning Engine v2"   << std::endl;
    std::cout << "============================================" << std::endl;

    json cfg = load_config("config.json");
    if (cfg.empty()) {
        std::cerr << "[ERROR] Cannot load config.json" << std::endl;
        return 1;
    }

    std::string conn_str = build_conn_str(cfg);
    database::Connection db(conn_str);
    if (!db.is_connected()) {
        std::cerr << "[ERROR] Cannot connect to database" << std::endl;
        return 1;
    }

    double      account_balance = 10000.0;
    int         update_count    = 0;
    std::string output_path     = "live_ticks.json";

    std::cout << "[OK] Connected | Starting reasoning loop every 1s..." << std::endl;
    std::cout << "[OK] Signals written to: signals table in DB"         << std::endl;
    std::cout << "[OK] Dashboard output: " << output_path               << std::endl << std::endl;

    while (true) {
        try {
            // ── Read all live symbols ──────────────────────────────
            PGresult* cur_res = db.execute(
                "SELECT symbol, bid, ask, spread, "
                "EXTRACT(EPOCH FROM (NOW() - last_updated)) AS seconds_ago "
                "FROM current WHERE bid > 0 ORDER BY symbol"
            );

            if (!cur_res) {
                std::this_thread::sleep_for(1s);
                continue;
            }

            json output;
            output["timestamp"]    = (long long)std::time(nullptr);
            output["update_count"] = ++update_count;
            output["ticks"]        = json::array();

            int n                = PQntuples(cur_res);
            int signals_this_tick = 0;

            for (int i = 0; i < n; i++) {
                try {
                    std::string symbol     = PQgetvalue(cur_res, i, 0);
                    double bid             = safe_stod(PQgetvalue(cur_res, i, 1));
                    double ask             = safe_stod(PQgetvalue(cur_res, i, 2));
                    double spread          = safe_stod(PQgetvalue(cur_res, i, 3));
                    double seconds_ago     = safe_stod(PQgetvalue(cur_res, i, 4));

                    if (bid <= 0.0) continue;   // skip zero-price rows

                    json sym_data = process_symbol(db, symbol, bid, ask, spread,
                                                   seconds_ago, account_balance);
                    output["ticks"].push_back(sym_data);

                    if (sym_data.value("signal", std::string("WAIT")) == "ENTER_LONG")
                        signals_this_tick++;

                } catch (const std::exception& e) {
                    std::cerr << "[WARN] Row " << i << ": " << e.what() << std::endl;
                } catch (...) {
                    std::cerr << "[WARN] Row " << i << ": unknown error, skipping" << std::endl;
                }
            }
            PQclear(cur_res);

            output["total_assets"]  = n;
            output["signals_count"] = signals_this_tick;

            // Write JSON — use replace error handler so NaN/Inf never crash dump()
            try {
                std::ofstream f(output_path);
                if (f.is_open()) {
                    f << output.dump(2, ' ', false,
                                     nlohmann::json::error_handler_t::replace);
                    f.close();
                }
            } catch (const std::exception& e) {
                std::cerr << "[WARN] JSON write: " << e.what() << std::endl;
            }

            // Log every 30 iterations
            if (update_count % 30 == 0) {
                std::cout << "[" << update_count << "] Assets: " << n
                          << " | Signals: " << signals_this_tick
                          << std::endl;
            }

        } catch (const std::exception& e) {
            std::cerr << "[ERROR] Main loop: " << e.what() << " — continuing" << std::endl;
        } catch (...) {
            std::cerr << "[ERROR] Main loop: unknown exception — continuing" << std::endl;
        }

        std::this_thread::sleep_for(1s);
    }

    return 0;
}
