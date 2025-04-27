from AlgorithmImports import *


class BuffettStrategy(QCAlgorithm):
    def Initialize(self):
        """Initialize the algorithm settings and portfolio parameters."""
        self.SetStartDate(2020, 1, 1)  # Set start date for backtest or live (YYYY, MM, DD)
        self.SetCash(100000)  # Set initial cash for backtesting
        # Define target stocks and allocation weights (sum should be <= 1.0)
        self.symbols = ["AAPL", "MSFT", "XOM", "GOLD", "NEE"]  # Example tickers
        self.targetAllocation = {
            "AAPL": 0.20,
            "MSFT": 0.20,
            "XOM": 0.15,  # Energy sector
            "GOLD": 0.15,  # Gold miner or commodity proxy
            "NEE": 0.10  # Renewable utilities
            # (Remaining weight can be kept as cash or assigned to others)
        }
        # Thresholds for triggers
        self.dca_threshold = 0.05  # 5% drop triggers DCA buy
        self.call_threshold = 0.10  # +10% above purchase price triggers covered call signal
        self.put_threshold = 0.10  # -10% below purchase price triggers protective put signal
        self.dca_fraction = 0.10  # Fractional additional shares to buy on DCA (10% of holdings)
        # Flags and trackers
        self.initial_alloc_done = False
        self.last_purchase_price = {}  # Tracks last buy price for each symbol

        # Add securities and set raw data mode for dividend events
        for ticker in self.symbols:
            equity = self.AddEquity(ticker, Resolution.Daily)
            equity.SetDataNormalizationMode(DataNormalizationMode.Raw)

        # Schedule initial allocation one minute after market open on first day
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.AfterMarketOpen(self.symbols[0], 1),
                         self.InitialAllocate)
        # Monthly rebalancing at market open
        self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.At(10, 0), self.RebalancePortfolio)
        # Daily portfolio summary logging before market close
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.BeforeMarketClose(self.symbols[0], 5),
                         self.LogPortfolioSummary)

    def InitialAllocate(self):
        """Perform initial purchases to reach target allocations."""
        if self.initial_alloc_done:
            return  # Only run once
        self.Log(f"{self.Time} >> Performing initial allocations")
        # Calculate and place orders to match target weights
        for ticker, weight in self.targetAllocation.items():
            self.SetHoldings(ticker, weight)
            # Record the price at which we first bought each stock
            price = self.Securities[ticker].Price
            self.last_purchase_price[ticker] = price
            self.Log(f"{self.Time} >> Bought {ticker} target weight {weight * 100:.0f}% at ${price:.2f}")
        self.initial_alloc_done = True

    def RebalancePortfolio(self):
        """Monthly rebalance to maintain target weights."""
        self.Log(f"{self.Time} >> Monthly rebalancing to target allocations")
        for ticker, weight in self.targetAllocation.items():
            self.SetHoldings(ticker, weight)
        # Update last_purchase_price to current prices after rebalancing
        for ticker in self.targetAllocation:
            self.last_purchase_price[ticker] = self.Securities[ticker].Price

    def OnData(self, data):
        """Handle new data points: dividends, DCA triggers, and option signals."""
        # Process dividend events for DRIP (reinvest dividends when paid)
        for ticker in self.symbols:
            if hasattr(data, "dividends"):
                dividend = data.dividends.get(self.Securities[ticker].Symbol)
                if dividend:
                    # Calculate cash received and buy as many shares as possible with it
                    shares_owned = self.Portfolio[ticker].Quantity
                    dividend_cash = dividend.Distribution * shares_owned
                    if dividend_cash > 0:
                        price = self.Securities[ticker].Price
                        # Determine number of shares to buy with dividend cash
                        shares_to_buy = int(dividend_cash / price)
                        if shares_to_buy > 0:
                            self.MarketOrder(ticker, shares_to_buy)
                            self.Log(
                                f"{self.Time} >> DRIP: Reinvested dividend ${dividend_cash:.2f} into {shares_to_buy} shares of {ticker} at ${price:.2f}")
                            # Update last purchase price to current if buying
                            self.last_purchase_price[ticker] = price

        # Daily checks for price-based decisions
        for ticker in self.symbols:
            # Skip if no trade bar for this symbol in current slice
            if not data.ContainsKey(self.Securities[ticker].Symbol):
                continue
            bar = data[self.Securities[ticker].Symbol]
            price = bar.Close

            # Dollar-Cost Averaging (buy on dips)
            if ticker in self.last_purchase_price:
                last_price = self.last_purchase_price[ticker]
                if price < last_price * (1 - self.dca_threshold):
                    # Calculate additional shares to buy (fraction of current holdings)
                    current_qty = self.Portfolio[ticker].Quantity
                    shares_to_buy = max(1, int(current_qty * self.dca_fraction))
                    self.MarketOrder(ticker, shares_to_buy)
                    self.last_purchase_price[ticker] = price
                    self.Log(
                        f"{self.Time} >> DCA: Bought additional {shares_to_buy} shares of {ticker} at ${price:.2f} (price dropped {self.dca_threshold * 100:.0f}% below last buy)")

            # Covered Call signal (stock up significantly)
            if ticker in self.last_purchase_price:
                if price > last_price * (1 + self.call_threshold):
                    self.Log(
                        f"{self.Time} >> SIGNAL: Consider selling covered call on {ticker} at ${price:.2f} (+{self.call_threshold * 100:.0f}% from last buy)")
                # Protective Put signal (stock down significantly)
                if price < last_price * (1 - self.put_threshold):
                    self.Log(
                        f"{self.Time} >> SIGNAL: Consider buying protective put on {ticker} at ${price:.2f} (-{self.put_threshold * 100:.0f}% from last buy)")

    def LogPortfolioSummary(self):
        """Log a brief summary of the portfolio (value and positions)."""
        total_value = self.Portfolio.TotalPortfolioValue
        cash = self.Portfolio.Cash
        self.Log(f"{self.Time} >> Portfolio Value: ${total_value:.2f}, Cash: ${cash:.2f}")
        for ticker in self.symbols:
            holding = self.Portfolio[ticker]
            if holding.Invested:
                self.Log(
                    f"   {ticker}: {holding.Quantity} shares, Avg Price: ${holding.AveragePrice:.2f}, Current: ${self.Securities[ticker].Price:.2f}")
