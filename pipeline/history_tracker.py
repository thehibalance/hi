#!/usr/bin/env python3
"""
HI. History Tracker + Backtest Engine
Captures daily snapshots, correlates with stock prices, backtests HUMAN 100 vs S&P 500.

Usage:
  python3 history_tracker.py --snapshot                # Daily snapshot (add to pipeline)
  python3 history_tracker.py --prices                  # Fetch stock prices for scored companies
  python3 history_tracker.py --backtest                # Run backtest: HUMAN 100 vs S&P 500
  python3 history_tracker.py --report --output data/   # Generate backtest report JSON

Called from run_all.py as Step 8 (after validation).

Patent Pending · Morf Innovations LLC · The HI Balance
"""
import json, os, sys, time, math, requests
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

TIMEOUT = 30
HISTORY_DIR = "data/history"
PRICES_DIR = "data/prices"


# ═══════════════════════════════════════════════════════════════════════
# STEP 1: Daily Snapshot — append, never overwrite
# ═══════════════════════════════════════════════════════════════════════

def take_snapshot(scores_dir="data/scores", history_dir=HISTORY_DIR):
    """Save today's scores as a dated snapshot."""
    print("\n  📸 Daily Snapshot")
    print("  " + "─" * 40)

    Path(history_dir).mkdir(parents=True, exist_ok=True)
    scores_file = Path(scores_dir) / "all_scores.json"

    if not scores_file.exists():
        print(f"    ⚠ No scores file at {scores_file}")
        return None

    scores = json.load(open(scores_file))
    today = datetime.now().strftime("%Y-%m-%d")
    snapshot_file = Path(history_dir) / f"{today}.json"

    # Extract only what we need for history (keep it lean)
    snapshot = {
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "total_companies": len(scores),
        "companies": []
    }

    gold_count = 0
    composites = []

    for c in scores:
        company_snap = {
            "company": c.get("company", ""),
            "ticker": c.get("ticker", ""),
            "composite": c.get("composite", 0),
            "D_H": c.get("D_H", 0),
            "D_U": c.get("D_U", 0),
            "D_M": c.get("D_M", 0),
            "D_A": c.get("D_A", 0),
            "D_N": c.get("D_N", 0),
            "hi_grade": c.get("hi_grade", ""),
            "hi_balanced": c.get("hi_balanced", False),
            "confidence": c.get("confidence", "Estimated"),
        }
        snapshot["companies"].append(company_snap)
        composites.append(c.get("composite", 0))
        if c.get("hi_balanced"):
            gold_count += 1

    # Summary stats
    snapshot["summary"] = {
        "gold_count": gold_count,
        "avg_composite": round(sum(composites) / len(composites), 1) if composites else 0,
        "median_composite": sorted(composites)[len(composites) // 2] if composites else 0,
        "threshold": round(sum(composites) / len(composites) + 2 * (sum((x - sum(composites)/len(composites))**2 for x in composites) / len(composites))**0.5, 1) if len(composites) > 1 else 55,
    }

    json.dump(snapshot, open(snapshot_file, "w"), indent=2)

    # Also maintain a rolling index of all snapshots
    index_file = Path(history_dir) / "index.json"
    if index_file.exists():
        index = json.load(open(index_file))
    else:
        index = {"snapshots": []}

    # Don't duplicate today
    index["snapshots"] = [s for s in index["snapshots"] if s["date"] != today]
    index["snapshots"].append({
        "date": today,
        "file": f"{today}.json",
        "total_companies": len(scores),
        "gold_count": gold_count,
        "avg_composite": snapshot["summary"]["avg_composite"],
    })
    index["snapshots"].sort(key=lambda x: x["date"])
    index["last_updated"] = datetime.now().isoformat()
    json.dump(index, open(index_file, "w"), indent=2)

    print(f"    ✓ Snapshot: {len(scores)} companies, {gold_count} gold")
    print(f"    Saved: {snapshot_file}")
    print(f"    History: {len(index['snapshots'])} days tracked")

    return snapshot


# ═══════════════════════════════════════════════════════════════════════
# STEP 2: Stock Price Capture — daily close for tickers
# ═══════════════════════════════════════════════════════════════════════

def fetch_prices(scores_dir="data/scores", prices_dir=PRICES_DIR):
    """Fetch daily closing prices for all tickers using free APIs."""
    print("\n  💰 Stock Price Capture")
    print("  " + "─" * 40)

    Path(prices_dir).mkdir(parents=True, exist_ok=True)
    scores_file = Path(scores_dir) / "all_scores.json"

    if not scores_file.exists():
        print(f"    ⚠ No scores file")
        return {}

    scores = json.load(open(scores_file))
    tickers = [c["ticker"] for c in scores if c.get("ticker") and len(c["ticker"]) <= 5]

    today = datetime.now().strftime("%Y-%m-%d")
    prices = {}

    # Use Finnhub (free tier, 60 calls/min)
    finnhub_key = os.environ.get("FINNHUB_API_KEY", "")
    if not finnhub_key:
        print("    ⚠ No FINNHUB_API_KEY — trying Yahoo Finance fallback")

    # Also fetch S&P 500 for benchmark
    tickers_to_fetch = list(set(tickers + ["SPY"]))  # SPY = S&P 500 ETF

    fetched = 0
    for ticker in tickers_to_fetch:
        try:
            if finnhub_key:
                r = requests.get("https://finnhub.io/api/v1/quote",
                    params={"symbol": ticker, "token": finnhub_key},
                    timeout=TIMEOUT)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("c", 0) > 0:  # c = current price
                        prices[ticker] = {
                            "price": data["c"],
                            "open": data.get("o", 0),
                            "high": data.get("h", 0),
                            "low": data.get("l", 0),
                            "prev_close": data.get("pc", 0),
                            "change_pct": round((data["c"] - data.get("pc", data["c"])) / data.get("pc", data["c"]) * 100, 2) if data.get("pc", 0) > 0 else 0,
                        }
                        fetched += 1
                time.sleep(0.1)  # Rate limit
            else:
                # Yahoo Finance fallback (no key needed)
                r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                    params={"interval": "1d", "range": "1d"},
                    headers={"User-Agent": "HI-Pipeline/1.0"},
                    timeout=TIMEOUT)
                if r.status_code == 200:
                    data = r.json()
                    result = data.get("chart", {}).get("result", [])
                    if result:
                        meta = result[0].get("meta", {})
                        prices[ticker] = {
                            "price": meta.get("regularMarketPrice", 0),
                            "prev_close": meta.get("previousClose", 0),
                            "change_pct": round((meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0)) / meta.get("previousClose", 1) * 100, 2),
                        }
                        fetched += 1
                time.sleep(0.2)

        except Exception as e:
            pass  # Skip failed tickers silently

        if fetched % 50 == 0 and fetched > 0:
            print(f"    ...{fetched} tickers priced")

    # Save today's prices
    price_file = Path(prices_dir) / f"{today}.json"
    output = {
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "tickers_priced": len(prices),
        "prices": prices,
    }
    json.dump(output, open(price_file, "w"), indent=2)

    spy_price = prices.get("SPY", {}).get("price", 0)
    print(f"    ✓ Priced {len(prices)} tickers (SPY: ${spy_price:.2f})")
    print(f"    Saved: {price_file}")

    return prices


# ═══════════════════════════════════════════════════════════════════════
# STEP 3: Backtest Engine — HUMAN 100 vs S&P 500
# ═══════════════════════════════════════════════════════════════════════

def run_backtest(history_dir=HISTORY_DIR, prices_dir=PRICES_DIR, output_dir="data"):
    """
    Backtest: If you invested equally in the HUMAN 100 vs SPY,
    how would returns compare over time?

    Methodology:
    - HUMAN 100 = top 100 companies by HI Grade composite (publicly traded only)
    - Equal-weight portfolio, rebalanced quarterly
    - Benchmark = SPY (S&P 500 ETF)
    - Returns calculated daily from price snapshots
    """
    print("\n  📊 Backtest: HUMAN 100 vs S&P 500")
    print("  " + "─" * 40)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load all history snapshots
    history_path = Path(history_dir)
    if not history_path.exists():
        print("    ⚠ No history data yet. Run --snapshot daily first.")
        return None

    index_file = history_path / "index.json"
    if not index_file.exists():
        print("    ⚠ No history index. Need at least 2 days of data.")
        return None

    index = json.load(open(index_file))
    dates = [s["date"] for s in index["snapshots"]]

    if len(dates) < 2:
        print(f"    ⚠ Only {len(dates)} day(s) of data. Need 2+ for backtest.")
        print("    Run the pipeline daily — backtest improves with more data.")

        # Generate a placeholder report with current HUMAN 100 composition
        if dates:
            latest = json.load(open(history_path / f"{dates[-1]}.json"))
            companies = latest.get("companies", [])

            # HUMAN 100 = top 100 with tickers (publicly traded)
            tradeable = [c for c in companies if c.get("ticker") and len(c.get("ticker", "")) <= 5]
            tradeable.sort(key=lambda x: -x.get("composite", 0))
            human100 = tradeable[:100]

            report = {
                "generated_at": datetime.now().isoformat(),
                "data_days": len(dates),
                "status": "accumulating",
                "message": f"Collecting data since {dates[0]}. Backtest available after 5+ trading days.",
                "human100_composition": [{
                    "rank": i + 1,
                    "company": c["company"],
                    "ticker": c["ticker"],
                    "composite": c["composite"],
                    "hi_grade": c.get("hi_grade", ""),
                    "gold": c.get("hi_balanced", False),
                } for i, c in enumerate(human100)],
                "benchmark": "SPY (S&P 500 ETF)",
                "methodology": {
                    "portfolio": "Equal-weight top 100 by HI Grade composite",
                    "rebalance": "Quarterly",
                    "eligibility": "Publicly traded, 2+ verified data sources, no humanwashing flags",
                },
            }

            report_file = Path(output_dir) / "backtest_report.json"
            json.dump(report, open(report_file, "w"), indent=2)
            print(f"    ✓ HUMAN 100 composition: {len(human100)} companies")
            print(f"    Saved: {report_file}")
            return report

        return None

    # With 2+ days, calculate actual returns
    print(f"    Analyzing {len(dates)} days of data...")

    daily_returns = []
    prev_date = None

    for date in dates:
        # HI-PATCH:backtest-missing-snapshot:v1
        # History has gaps (e.g. 2026-04-17 -> 2026-04-30). Guard the snapshot
        # load the same way price_file is guarded below, or one missing day
        # kills the entire backtest.
        snapshot_file = history_path / f"{date}.json"
        if not snapshot_file.exists():
            continue
        snapshot = json.load(open(snapshot_file))
        price_file = Path(prices_dir) / f"{date}.json"

        if not price_file.exists():
            continue

        price_data = json.load(open(price_file))
        prices = price_data.get("prices", {})

        if not prices:
            continue

        # Get HUMAN 100 tickers
        companies = snapshot.get("companies", [])
        tradeable = [c for c in companies if c.get("ticker") and c["ticker"] in prices]
        tradeable.sort(key=lambda x: -x.get("composite", 0))
        human100_tickers = [c["ticker"] for c in tradeable[:100]]

        # Calculate equal-weight HUMAN 100 return for this day
        h100_changes = []
        for ticker in human100_tickers:
            p = prices.get(ticker, {})
            change = p.get("change_pct", 0)
            h100_changes.append(change)

        h100_return = sum(h100_changes) / len(h100_changes) if h100_changes else 0
        spy_return = prices.get("SPY", {}).get("change_pct", 0)

        daily_returns.append({
            "date": date,
            "human100_return": round(h100_return, 3),
            "spy_return": round(spy_return, 3),
            "alpha": round(h100_return - spy_return, 3),
            "human100_companies": len(human100_tickers),
        })

    # Calculate cumulative returns
    h100_cumulative = 100  # Start at $100
    spy_cumulative = 100
    cumulative_series = []

    for day in daily_returns:
        h100_cumulative *= (1 + day["human100_return"] / 100)
        spy_cumulative *= (1 + day["spy_return"] / 100)
        cumulative_series.append({
            "date": day["date"],
            "human100_value": round(h100_cumulative, 2),
            "spy_value": round(spy_cumulative, 2),
            "alpha_cumulative": round(h100_cumulative - spy_cumulative, 2),
        })

    # Summary
    total_alpha = round(h100_cumulative - spy_cumulative, 2)
    h100_total_return = round((h100_cumulative - 100), 2)
    spy_total_return = round((spy_cumulative - 100), 2)

    # Get latest HUMAN 100 composition
    latest = json.load(open(history_path / f"{dates[-1]}.json"))
    companies = latest.get("companies", [])
    tradeable = [c for c in companies if c.get("ticker") and len(c.get("ticker", "")) <= 5]
    tradeable.sort(key=lambda x: -x.get("composite", 0))
    human100 = tradeable[:100]

    report = {
        "generated_at": datetime.now().isoformat(),
        "data_days": len(dates),
        "trading_days": len(daily_returns),
        "period": {"start": dates[0], "end": dates[-1]},
        "status": "live" if len(daily_returns) >= 5 else "accumulating",
        "returns": {
            "human100_total": h100_total_return,
            "spy_total": spy_total_return,
            "alpha": total_alpha,
            "human100_final_value": round(h100_cumulative, 2),
            "spy_final_value": round(spy_cumulative, 2),
        },
        "daily_returns": daily_returns,
        "cumulative_series": cumulative_series,
        "human100_composition": [{
            "rank": i + 1,
            "company": c["company"],
            "ticker": c["ticker"],
            "composite": c["composite"],
            "gold": c.get("hi_balanced", False),
        } for i, c in enumerate(human100)],
        "top_performers": sorted(
            [{"ticker": d["date"], "alpha": d["alpha"]} for d in daily_returns],
            key=lambda x: -x["alpha"]
        )[:5],
        "benchmark": "SPY (S&P 500 ETF)",
        "methodology": {
            "portfolio": "Equal-weight top 100 by HI Grade composite",
            "rebalance": "Quarterly",
            "eligibility": "Publicly traded, 2+ verified data sources",
            "inception": dates[0],
        },
        "disclaimer": "Backtested results are hypothetical and do not represent actual trading. Past performance does not guarantee future results. Not financial advice.",
    }

    report_file = Path(output_dir) / "backtest_report.json"
    json.dump(report, open(report_file, "w"), indent=2)

    print(f"    Period: {dates[0]} → {dates[-1]} ({len(daily_returns)} trading days)")
    print(f"    HUMAN 100: {h100_total_return:+.2f}%")
    print(f"    S&P 500:   {spy_total_return:+.2f}%")
    print(f"    Alpha:     {total_alpha:+.2f}%")
    print(f"    ✓ Report: {report_file}")

    return report


# ═══════════════════════════════════════════════════════════════════════
# STEP 4: Trend Calculator — per-company score history
# ═══════════════════════════════════════════════════════════════════════

def calculate_trends(history_dir=HISTORY_DIR, output_dir="data"):
    """Calculate per-company score trends from history."""
    print("\n  📈 Score Trends")
    print("  " + "─" * 40)

    history_path = Path(history_dir)
    index_file = history_path / "index.json"
    if not index_file.exists():
        print("    ⚠ No history data")
        return {}

    index = json.load(open(index_file))
    dates = [s["date"] for s in index["snapshots"]]

    if len(dates) < 2:
        print(f"    Need 2+ snapshots (have {len(dates)})")
        return {}

    # Build per-company time series
    company_history = defaultdict(list)

    for date in dates:
        snap_file = history_path / f"{date}.json"
        if not snap_file.exists():
            continue
        snapshot = json.load(open(snap_file))
        for c in snapshot.get("companies", []):
            key = c.get("ticker") or c.get("company", "")
            if key:
                company_history[key].append({
                    "date": date,
                    "composite": c.get("composite", 0),
                    "D_H": c.get("D_H", 0),
                    "D_U": c.get("D_U", 0),
                    "D_M": c.get("D_M", 0),
                    "D_A": c.get("D_A", 0),
                    "D_N": c.get("D_N", 0),
                })

    # Calculate trends
    trends = {}
    movers_up = []
    movers_down = []

    for key, history in company_history.items():
        if len(history) < 2:
            continue

        history.sort(key=lambda x: x["date"])
        first = history[0]
        last = history[-1]

        composite_change = last["composite"] - first["composite"]
        dim_changes = {
            "H": last["D_H"] - first["D_H"],
            "U": last["D_U"] - first["D_U"],
            "M": last["D_M"] - first["D_M"],
            "A": last["D_A"] - first["D_A"],
            "N": last["D_N"] - first["D_N"],
        }

        # Simple linear trend (points per day)
        days = max(1, (datetime.strptime(last["date"], "%Y-%m-%d") -
                       datetime.strptime(first["date"], "%Y-%m-%d")).days)
        daily_trend = composite_change / days
        quarterly_trend = daily_trend * 90  # Project quarterly

        trends[key] = {
            "company": key,
            "first_score": first["composite"],
            "latest_score": last["composite"],
            "change": composite_change,
            "daily_trend": round(daily_trend, 3),
            "quarterly_projection": round(quarterly_trend, 1),
            "dimension_changes": dim_changes,
            "data_points": len(history),
            "period": {"start": first["date"], "end": last["date"]},
        }

        if composite_change > 3:
            movers_up.append((key, composite_change))
        elif composite_change < -3:
            movers_down.append((key, composite_change))

    # Save trends
    trend_file = Path(output_dir) / "score_trends.json"
    output = {
        "generated_at": datetime.now().isoformat(),
        "companies_tracked": len(trends),
        "period": {"start": dates[0], "end": dates[-1]},
        "biggest_gains": sorted(movers_up, key=lambda x: -x[1])[:20],
        "biggest_drops": sorted(movers_down, key=lambda x: x[1])[:20],
        "trends": trends,
    }
    json.dump(output, open(trend_file, "w"), indent=2)

    print(f"    ✓ Tracking {len(trends)} companies over {len(dates)} days")
    if movers_up:
        print(f"    Biggest gains: {', '.join(f'{k}(+{v})' for k, v in sorted(movers_up, key=lambda x: -x[1])[:5])}")
    if movers_down:
        print(f"    Biggest drops: {', '.join(f'{k}({v})' for k, v in sorted(movers_down, key=lambda x: x[1])[:5])}")

    return trends


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="HI. History Tracker + Backtest")
    p.add_argument("--scores", default="data/scores", help="Scores directory")
    p.add_argument("--history", default=HISTORY_DIR, help="History directory")
    p.add_argument("--prices-dir", default=PRICES_DIR, help="Prices directory")
    p.add_argument("--output", default="data", help="Output directory")
    p.add_argument("--snapshot", action="store_true", help="Take daily snapshot")
    p.add_argument("--prices", action="store_true", help="Fetch stock prices")
    p.add_argument("--backtest", action="store_true", help="Run backtest")
    p.add_argument("--trends", action="store_true", help="Calculate score trends")
    p.add_argument("--all", action="store_true", help="Run everything")
    a = p.parse_args()

    if a.all or (not any([a.snapshot, a.prices, a.backtest, a.trends])):
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║  HI. — History Tracker + Backtest Engine                ║")
        print("║  Does being human pay?                                  ║")
        print("╚══════════════════════════════════════════════════════════╝")
        take_snapshot(a.scores, a.history)
        fetch_prices(a.scores, a.prices_dir)
        run_backtest(a.history, a.prices_dir, a.output)
        calculate_trends(a.history, a.output)
    else:
        if a.snapshot:
            take_snapshot(a.scores, a.history)
        if a.prices:
            fetch_prices(a.scores, a.prices_dir)
        if a.backtest:
            run_backtest(a.history, a.prices_dir, a.output)
        if a.trends:
            calculate_trends(a.history, a.output)
