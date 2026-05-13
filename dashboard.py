import os
from flask import Flask, render_template_string
import sqlite3
import json

app = Flask(__name__)
DB_PATH = "trades.db"
ACCOUNT_SIZE = 25000.00

def get_trades():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM trades ORDER BY created_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_stats(trades):
    closed = [t for t in trades if t["status"] == "closed"]
    if not closed:
        return {}
    wins   = [t for t in closed if t["pnl"] and t["pnl"] > 0]
    losses = [t for t in closed if t["pnl"] and t["pnl"] <= 0]
    win_rate      = len(wins) / len(closed)
    avg_win       = sum(t["pnl"] for t in wins) / len(wins) if wins else 0
    avg_loss      = sum(t["pnl"] for t in losses) / len(losses) if losses else 0
    total_pnl     = sum(t["pnl"] for t in closed if t["pnl"])
    profit_factor = abs(sum(t["pnl"] for t in wins) / sum(t["pnl"] for t in losses)) if losses else 0
    expectancy    = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
    return {
        "total_trades"  : len(closed),
        "win_rate"      : f"{win_rate:.1%}",
        "avg_win"       : f"${avg_win:.2f}",
        "avg_loss"      : f"${avg_loss:.2f}",
        "profit_factor" : f"{profit_factor:.2f}",
        "expectancy"    : f"${expectancy:.2f}",
        "total_pnl"     : f"${total_pnl:.2f}",
    }

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Options Bot Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: -apple-system, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        h1 { color: #1a1a1a; margin-bottom: 4px; }
        .subtitle { color: #666; margin-bottom: 24px; font-size: 14px; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 24px; }
        .card { background: white; border-radius: 10px; padding: 16px; border: 1px solid #e0e0e0; }
        .card-label { font-size: 12px; color: #888; margin-bottom: 6px; }
        .card-value { font-size: 22px; font-weight: 500; color: #1a1a1a; }
        .card-value.green { color: #2e7d32; }
        .card-value.red { color: #c62828; }
        .section { background: white; border-radius: 10px; padding: 20px; margin-bottom: 16px; border: 1px solid #e0e0e0; }
        .section h2 { margin: 0 0 16px; font-size: 16px; color: #1a1a1a; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { text-align: left; padding: 8px; border-bottom: 2px solid #f0f0f0; color: #888; font-weight: 500; }
        td { padding: 8px; border-bottom: 1px solid #f5f5f5; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
        .badge.closed { background: #e8f5e9; color: #2e7d32; }
        .badge.open { background: #e3f2fd; color: #1565c0; }
        .badge.stopped { background: #fce4ec; color: #c62828; }
        .pos { color: #2e7d32; }
        .neg { color: #c62828; }
        canvas { max-height: 280px; }
        .no-data { color: #aaa; font-size: 14px; padding: 20px 0; }
    </style>
</head>
<body>
    <h1>Options paper trading bot</h1>
    <div class="subtitle">Paper account: $25,000 | All figures in USD</div>

    <div class="cards">
        <div class="card"><div class="card-label">Total trades</div><div class="card-value">{{ stats.get('total_trades', 0) }}</div></div>
        <div class="card"><div class="card-label">Win rate</div><div class="card-value">{{ stats.get('win_rate', 'N/A') }}</div></div>
        <div class="card"><div class="card-label">Profit factor</div><div class="card-value">{{ stats.get('profit_factor', 'N/A') }}</div></div>
        <div class="card"><div class="card-label">Expectancy</div><div class="card-value">{{ stats.get('expectancy', 'N/A') }}</div></div>
        <div class="card"><div class="card-label">Total P&L</div>
            <div class="card-value {% if stats.get('total_pnl', '$0.00').startswith('$-') %}red{% else %}green{% endif %}">
                {{ stats.get('total_pnl', '$0.00') }}
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Equity curve</h2>
        {% if equity_dates %}
        <canvas id="equityChart"></canvas>
        {% else %}
        <div class="no-data">No closed trades yet. Log some paper trades to see your equity curve.</div>
        {% endif %}
    </div>

    <div class="section">
        <h2>Trade journal</h2>
        {% if trades %}
        <table>
            <tr>
                <th>Date</th><th>Symbol</th><th>Type</th><th>Strike</th>
                <th>Entry</th><th>Exit</th><th>Status</th><th>P&L</th>
            </tr>
            {% for t in trades %}
            <tr>
                <td>{{ t.trade_date }}</td>
                <td><strong>{{ t.symbol }}</strong></td>
                <td>{{ t.option_type }}</td>
                <td>${{ t.strike }}</td>
                <td>${{ t.entry_price }}</td>
                <td>{{ '$'+str(t.exit_price) if t.exit_price else '—' }}</td>
                <td><span class="badge {{ t.status }}">{{ t.status }}</span></td>
                <td class="{{ 'pos' if t.pnl and t.pnl > 0 else 'neg' }}">
                    {{ '$'+'{:.2f}'.format(t.pnl) if t.pnl else '—' }}
                </td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <div class="no-data">No trades logged yet.</div>
        {% endif %}
    </div>

    <script>
        const dates  = {{ equity_dates | tojson }};
        const values = {{ equity_values | tojson }};
        if (dates.length > 0) {
            new Chart(document.getElementById('equityChart'), {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Account value',
                        data: values,
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33,150,243,0.08)',
                        borderWidth: 2,
                        pointRadius: 4,
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: false, ticks: { callback: v => '$'+v.toLocaleString() } }
                    }
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    trades = get_trades()
    stats  = get_stats(trades)
    closed = [t for t in trades if t["status"] == "closed" and t["pnl"]]
    closed_sorted = sorted(closed, key=lambda x: x["trade_date"])
    equity = ACCOUNT_SIZE
    equity_dates  = []
    equity_values = []
    for t in closed_sorted:
        equity += t["pnl"]
        equity_dates.append(t["trade_date"])
        equity_values.append(round(equity, 2))
    return render_template_string(HTML, trades=trades, stats=stats,
                                   equity_dates=equity_dates, equity_values=equity_values,
                                   str=str)

if __name__ == "__main__":
    print("Dashboard running at http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))