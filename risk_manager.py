from dataclasses import dataclass
from typing import Optional

ACCOUNT_SIZE = 25000.00  # your paper trading account size

@dataclass
class TradeSetup:
    symbol: str
    option_type: str
    strike: float
    expiry: str
    contracts: int
    entry_price: float
    stop_loss: float
    profit_target: float
    bid: float
    ask: float
    open_interest: int
    strategy: str
    notes: str = ""

@dataclass
class ApprovalResult:
    approved: bool
    reason: str
    max_risk: float = 0.0

class RiskManager:
    def __init__(self, account_size: float = ACCOUNT_SIZE,
                 max_risk_pct: float = 0.02,
                 max_daily_loss_pct: float = 0.05,
                 max_trades_per_day: int = 3):

        self.account_size = account_size
        self.max_risk_pct = max_risk_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_trades_per_day = max_trades_per_day
        self.daily_loss = 0.0
        self.trades_today = 0

    def approve(self, setup: TradeSetup) -> ApprovalResult:
        max_dollar_risk = self.account_size * self.max_risk_pct
        max_daily_loss  = self.account_size * self.max_daily_loss_pct
        trade_risk      = setup.contracts * setup.entry_price * 100

        # 1. Daily loss limit
        if self.daily_loss >= max_daily_loss:
            return ApprovalResult(
                approved=False,
                reason=f"Daily loss limit hit (${max_daily_loss:.0f}). No more trades today."
            )

        # 2. Max trades per day
        if self.trades_today >= self.max_trades_per_day:
            return ApprovalResult(
                approved=False,
                reason=f"Max {self.max_trades_per_day} trades per day reached. Stop overtrading."
            )

        # 3. Position size — never risk more than 2%
        if trade_risk > max_dollar_risk:
            return ApprovalResult(
                approved=False,
                reason=f"Trade risks ${trade_risk:.0f}. Max allowed: ${max_dollar_risk:.0f}. Reduce contracts."
            )

        # 4. Stop loss required
        if setup.stop_loss is None or setup.stop_loss <= 0:
            return ApprovalResult(
                approved=False,
                reason="No stop loss defined. Every trade requires a stop loss."
            )

        # 5. Profit target required
        if setup.profit_target is None or setup.profit_target <= 0:
            return ApprovalResult(
                approved=False,
                reason="No profit target defined. Every trade requires a profit target."
            )

        # 6. Reward/risk ratio minimum 1:1
        reward = (setup.profit_target - setup.entry_price) * setup.contracts * 100
        risk   = (setup.entry_price - setup.stop_loss)     * setup.contracts * 100
        if risk <= 0 or reward / risk < 1.0:
            return ApprovalResult(
                approved=False,
                reason=f"Reward/risk ratio is {reward/risk:.2f}. Minimum is 1.0. Adjust your targets."
            )

        # 7. Liquidity — bid/ask spread check
        mid = (setup.bid + setup.ask) / 2
        spread_pct = (setup.ask - setup.bid) / mid if mid > 0 else 1.0
        if spread_pct > 0.10:
            return ApprovalResult(
                approved=False,
                reason=f"Bid/ask spread is {spread_pct:.1%}. Too wide (max 10%). Illiquid option."
            )

        # 8. Open interest check
        if setup.open_interest < 100:
            return ApprovalResult(
                approved=False,
                reason=f"Open interest is {setup.open_interest}. Too low (min 100). Illiquid option."
            )

        # All checks passed
        self.trades_today += 1
        return ApprovalResult(
            approved=True,
            reason="All risk checks passed. Trade approved for paper execution.",
            max_risk=trade_risk
        )

    def record_loss(self, amount: float):
        self.daily_loss += abs(amount)

    def reset_daily(self):
        self.daily_loss = 0.0
        self.trades_today = 0


if __name__ == "__main__":
    rm = RiskManager(account_size=25000)

    print("=" * 55)
    print("RISK MANAGER TEST")
    print("=" * 55)

    # Test 1 — good trade, should pass
    good_trade = TradeSetup(
        symbol="AAPL",
        option_type="call",
        strike=200.0,
        expiry="2026-06-20",
        contracts=1,
        entry_price=3.50,
        stop_loss=1.75,
        profit_target=7.00,
        bid=3.40,
        ask=3.60,
        open_interest=500,
        strategy="momentum_breakout"
    )
    result = rm.approve(good_trade)
    print(f"\nTest 1 — Good trade")
    print(f"Approved: {result.approved}")
    print(f"Reason:   {result.reason}")

    # Test 2 — no stop loss, should fail
    bad_trade = TradeSetup(
        symbol="TSLA",
        option_type="call",
        strike=250.0,
        expiry="2026-06-20",
        contracts=1,
        entry_price=5.00,
        stop_loss=0,
        profit_target=10.00,
        bid=4.80,
        ask=5.20,
        open_interest=300,
        strategy="momentum_breakout"
    )
    result2 = rm.approve(bad_trade)
    print(f"\nTest 2 — No stop loss")
    print(f"Approved: {result2.approved}")
    print(f"Reason:   {result2.reason}")

    # Test 3 — too much risk, should fail
    risky_trade = TradeSetup(
        symbol="SPY",
        option_type="call",
        strike=500.0,
        expiry="2026-06-20",
        contracts=10,
        entry_price=8.00,
        stop_loss=4.00,
        profit_target=16.00,
        bid=7.80,
        ask=8.20,
        open_interest=1000,
        strategy="momentum_breakout"
    )
    result3 = rm.approve(risky_trade)
    print(f"\nTest 3 — Too much risk (10 contracts)")
    print(f"Approved: {result3.approved}")
    print(f"Reason:   {result3.reason}")

    # Test 4 — illiquid option, should fail
    illiquid_trade = TradeSetup(
        symbol="XYZ",
        option_type="call",
        strike=50.0,
        expiry="2026-06-20",
        contracts=1,
        entry_price=2.00,
        stop_loss=1.00,
        profit_target=4.00,
        bid=1.50,
        ask=2.50,
        open_interest=50,
        strategy="momentum_breakout"
    )
    result4 = rm.approve(illiquid_trade)
    print(f"\nTest 4 — Illiquid option (wide spread + low OI)")
    print(f"Approved: {result4.approved}")
    print(f"Reason:   {result4.reason}")

    print("\n" + "=" * 55)
