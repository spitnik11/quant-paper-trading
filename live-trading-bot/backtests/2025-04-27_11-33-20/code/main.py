from AlgorithmImports import *

class BuffettStrategy(QCAlgorithm):
    def Initialize(self):
        """Initialize the algorithm settings and portfolio parameters."""
        self.SetStartDate(2020, 1, 1)
        self.SetCash(100000)

        # Define target stocks and allocation weights
        self.symbols = ["AAPL", "MSFT", "XOM", "GOLD", "NEE"]
        self.target_allocation = {
            "AAPL": 0.20,
            "MSFT": 0.20,
            "XOM": 0.15,
            "GOLD": 0.15,
            "NEE": 0.10
        }

        # Thresholds for triggers
        self.dca_threshold = 0.05
        self.call_threshold = 0.10
        self.put_threshold = 0.10
        self.dca_fraction = 0.10

        # Flags and trackers
        self.initial_alloc_done = False
        self.last_purchase_price = {}

        # Add securities and set raw data mode
        self.symbol_objects = {}
        for ticker in self.symbols:
            equity = self.AddEquity(ticker, Resolution.Daily)
            equity.SetDataNormalizationMode(DataNormalizationMode.Raw)
            self.symbol_objects[ticker] = equity.Symbol

        # Set warm-up period
        self.SetWarmUp(timedelta(days=5))

        # Schedule events
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.AfterMarketOpen(self.symbol_objects["AAPL"], 1), self.InitialAllocate)
        self.Schedule.On(self.DateRules.MonthStart(self.symbol_objects["AAPL"]), self.TimeRules.At(10, 0), self.RebalancePortfolio)
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.BeforeMarketClose(self.symbol_objects["AAPL"], 5), self.LogPortfolioSummary)

    def InitialAllocate(self):
        """Perform initial purchases to reach target allocations."""
        if self.initial_alloc_done or self.IsWarmingUp:
            return

        self.Log(f"{self.Time} >> Performing initial allocations")
        for ticker, weight in self.target_allocation.items():
            symbol = self.symbol_objects[ticker]
            if not self.Securities[symbol].HasData:
                self.Log(f"{self.Time} >> Skipping {ticker}: No data available.")
                continue
            self.SetHoldings(symbol, weight)
            price = self.Securities[symbol].Price
            self.last_purchase_price[ticker] = price
            self.Log(f"{self.Time} >> Bought {ticker} target weight {weight*100:.0f}% at ${price:.2f}")
        self.initial_alloc_done = True

    def RebalancePortfolio(self):
        """Monthly rebalance to maintain target weights."""
        if self.IsWarmingUp:
            return

        self.Log(f"{self.Time} >> Monthly rebalancing to target allocations")
        for ticker, weight in self.target_allocation.items():
            symbol = self.symbol_objects[ticker]
            if not self.Securities[symbol].HasData:
                self.Log(f"{self.Time} >> Skipping {ticker}: No data available.")
                continue
            self.SetHoldings(symbol, weight)
            self.last_purchase_price[ticker] = self.Securities[symbol].Price

    def OnData(self, data):
        """Handle new data points: dividends, DCA triggers, and option signals."""
        if self.IsWarmingUp:
            return

        # Process dividend events for DRIP
        for ticker in self.symbols:
            symbol = self.symbol_objects[ticker]
            if data.Dividends.ContainsKey(symbol):
                dividend = data.Dividends[symbol]
                shares_owned = self.Portfolio[symbol].Quantity
                dividend_cash = dividend.Distribution * shares_owned
                if dividend_cash > 0:
                    price = self.Securities[symbol].Price
                    shares_to_buy = int(dividend_cash / price)
                    if shares_to_buy > 0:
                        self.MarketOrder(symbol, shares_to_buy)
                        self.Log(f"{self.Time} >> DRIP: Reinvested dividend ${dividend_cash:.2f} into {shares_to_buy} shares of {ticker} at ${price:.2f}")
                        self.last_purchase_price[ticker] = price

        # Daily checks for price-based decisions
        for ticker in self.symbols:
            symbol = self.symbol_objects[ticker]
            if not data.ContainsKey(symbol) or data[symbol] is None:
                continue
            price = data[symbol].Close

            if ticker in self.last_purchase_price:
                last_price = self.last_purchase_price[ticker]
                if price < last_price * (1 - self.dca_threshold):
                    current_qty = self.Portfolio[symbol].Quantity
                    shares_to_buy = max(1, int(current_qty * self.dca_fraction))
                    self.MarketOrder(symbol, shares_to_buy)
                    self.last_purchase_price[ticker] = price
                    self.Log(f"{self.Time} >> DCA: Bought additional {shares_to_buy} shares of {ticker} at ${price:.2f} (price dropped {self.dca_threshold*100:.0f}% below last buy)")

                if price > last_price * (1 + self.call_threshold):
                    self.Log(f"{self.Time} >> SIGNAL: Consider selling covered call on {ticker} at ${price:.2f} (+{self.call_threshold*100:.0f}% from last buy)")

                if price < last_price * (1 - self.put_threshold):
                    self.Log(f"{self.Time} >> SIGNAL: Consider buying protective put on {ticker} at ${price:.2f} (-{self.put_threshold*100:.0f}% from last buy)")

    def LogPortfolioSummary(self):
        """Log a brief summary of the portfolio."""
        total_value = self.Portfolio.TotalPortfolioValue
        cash = self.Portfolio.Cash
        self.Log(f"{self.Time} >> Portfolio Value: ${total_value:.2f}, Cash: ${cash:.2f}")
        for ticker in self.symbols:
            symbol = self.symbol_objects[ticker]
            holding = self.Portfolio[symbol]
            if holding.Invested:
                self.Log(f"   {ticker}: {holding.Quantity} shares, Avg Price: ${holding.AveragePrice:.2f}, Current: ${self.Securities[symbol].Price:.2f}")
