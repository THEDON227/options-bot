from flask import Flask, render_template_string
from journal import init_db, get_all_trades
import os

app = Flask(__name__)

def get_trades():
    init_db()
    return get_all_trades()

def get_stats(trades):
    closed = [t for t in trades if t.get("status") == "closed"]

    total_pnl = sum(float(t.get("pnl") or 0) for t in closed)
    wins = [t for t in closed if float(t.get("pnl") or 0) > 0]
    losses = [t for t in closed if float(t.get("pnl") or 0) < 0]

    gross_profit = sum(float(t.get("pnl") or 0) for t in wins)
    gross_loss = abs(sum(float(t.get("pnl") or 0) for t in losses))

    return {
        "total_trades": len(trades),
        "win_rate": f"{(len(wins) / len(closed) * 100):.1f}%" if closed else "N/A",
        "profit_factor": f"{(gross_profit / gross_loss):.2f}" if gross_loss else "N/A",
        "expectancy": f"${(total_pnl / len(closed)):.2f}" if closed else "N/A",
        "total_pnl": total_pnl
    }

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Options Bot Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background:#f5f5f5; margin:0; padding:30px; }
        h1 { margin-bottom:5px; }
        .subtitle { color:#666; margin-bottom:30px; }
        .cards { display:flex; gap:20px; margin-bottom:30px; flex-wrap:wrap; }
        .card { background:white; padding:22px; border-radius:10px; min-width:180px; box-shadow:0 1px 4px rgba(0,0,0,.1); }
        .card-label { color:#777; font-size:14px; margin-bottom:10px; }
        .card-value { font-size:28px; font-weight:bold; }
        .green { color:#1f7a30; }
        .section { background:white; padding:25px; border-radius:10px; margin-bottom:25px; box-shadow:0 1px 4px rgba(0,0,0,.1); }
        table { width:100%; border-collapse:collapse; margin-top:15px; }
        th, td { padding:12px; border-bottom:1px solid #ddd; text-align:left; }
        th { background:#f0f0f0; }
        .no-data { color:#999; margin-top:20px; }
    </style>
</head>
<body>
    <h1>Options paper trading bot</h1>
    <div class="subtitle">Paper account: $25,000 | All figures in USD</div>

    <div class="cards">
        <div class="card"><div class="card-label">Total trades</div><div class="card-value">{{ stats.total_trades }}</div></div>
        <div class="card"><div class="card-label">Win rate</div><div class="card-value">{{ stats.win_rate }}</div></div>
        <div class="card"><div class="card-label">Profit factor</div><div class="card-value">{{ stats.profit_factor }}</div></div>
        <div class="card"><div class="card-label">Expectancy</div><div class="card-value">{{ stats.expectancy }}</div></div>
        <div class="card"><div class="card-label">Total P&L</div><div class="card-value green">${{ "%.2f"|format(stats.total_pnl) }}</div></div>
    </div>

    <div class="section">
        <h2>Equity curve</h2>
        <div class="no-data">Closed trades will appear here after trades are closed.</div>
    </div>

    <div class="section">
        <h2>Trade journal</h2>
        {% if trades %}
        <table>
            <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Symbol</th>
                <th>Type</th>
                <th>Strike</th>
                <th>Entry</th>
                <th>Status</th>
                <th>P&L</th>
            </tr>
            {% for t in trades %}
            <tr>
                <td>{{ t.id }}</td>
                <td>{{ t.created_at }}</td>
                <td>{{ t.symbol }}</td>
                <td>{{ t.option_type }}</td>
                <td>{{ t.strike }}</td>
                <td>{{ t.entry_price }}</td>
                <td>{{ t.status }}</td>
                <td>{{ t.pnl }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <div class="no-data">No trades logged yet.</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    trades = get_trades()
    stats = get_stats(trades)
    return render_template_string(HTML, trades=trades, stats=stats)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
