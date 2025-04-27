from AlgorithmImports import *

class BuffettStrategy(QCAlgorithm):
    def initialize(self):
        """Initialize the algorithm settings and portfolio parameters."""
        self.set_start_date(2020, 1, 1)
        self.set_cash(100000)

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
        for ticker in self.symbols:
            equity = self.add_equity(ticker, Resolution.Daily)
            equity.set_data_normalization_mode(DataNormalizationMode.Raw)

        # Set warm-up period
        self.set_warm_up(timedelta(days=5))

        # Schedule events
        self.schedule.on(self.date_rules.every_day(), self.time_rules.after_market_open(self.symbols[0], 1), self.initial_allocate)
        self.schedule.on(self.date_rules.month_start(self.symbols[0]), self.time_rules.at(10, 0), self.rebalance_portfolio)
        self.schedule.on(self.date_rules.every_day(), self.time_rules.before_market_close(self.symbols[0], 5), self.log_portfolio_summary)

    def initial_allocate(self):
        """Perform initial purchases to reach target allocations."""
        if self.initial_alloc_done or self.is_warming_up:
            return

        self.log(f"{self.time} >> Performing initial allocations")
        for ticker, weight in self.target_allocation.items():
            symbol = self.symbol(ticker)
            if not self.securities[symbol].has_data:
                self.log(f"{self.time} >> Skipping {ticker}: No data available.")
                continue
            self.set_holdings(symbol, weight)
            price = self.securities[symbol].price
            self.last_purchase_price[ticker] = price
            self.log(f"{self.time} >> Bought {ticker} target weight {weight*100:.0f}% at ${price:.2f}")
        self.initial_alloc_done = True

    def rebalance_portfolio(self):
        """Monthly rebalance to maintain target weights."""
        self.log(f"{self.time} >> Monthly rebalancing to target allocations")
        for ticker, weight in self.target_allocation.items():
            symbol = self.symbol(ticker)
            if not self.securities[symbol].has_data:
                self.log(f"{self.time} >> Skipping {ticker}: No data available.")
                continue
            self.set_holdings(symbol, weight)
            self.last_purchase_price[ticker] = self.securities[symbol].price

    def on_data(self, data):
        """Handle new data points: dividends, DCA triggers, and option signals."""
        if self.is_warming_up:
            return

        # Process dividend events for DRIP
        for ticker in self.symbols:
            symbol = self.symbol(ticker)
            if data.dividends.contains_key(symbol):
                dividend = data.dividends[symbol]
                shares_owned = self.portfolio[symbol].quantity
                dividend_cash = dividend.distribution * shares_owned
                if dividend_cash > 0:
                    price = self.securities[symbol].price
                    shares_to_buy = int(dividend_cash / price)
                    if shares_to_buy > 0:
                        self.market_order(symbol, shares_to_buy)
                        self.log(f"{self.time} >> DRIP: Reinvested dividend ${dividend_cash:.2f} into {shares_to_buy} shares of {ticker} at ${price:.2f}")
                        self.last_purchase_price[ticker] = price

        # Daily checks for price-based decisions
        for ticker in self.symbols:
            symbol = self.symbol(ticker)
            if not data.contains_key(symbol):
                continue
            price = data[symbol].close

            if ticker in self.last_purchase_price:
                last_price = self.last_purchase_price[ticker]
                if price < last_price * (1 - self.dca_threshold):
                    current_qty = self.portfolio[symbol].quantity
                    shares_to_buy = max(1, int(current_qty * self.dca_fraction))
                    self.market_order(symbol, shares_to_buy)
                    self.last_purchase_price[ticker] = price
                    self.log(f"{self.time} >> DCA: Bought additional {shares_to_buy} shares of {ticker} at ${price:.2f} (price dropped {self.dca_threshold*100:.0f}% below last buy)")

                if price > last_price * (1 + self.call_threshold):
                    self.log(f"{self.time} >> SIGNAL: Consider selling covered call on {ticker} at ${price:.2f} (+{self.call_threshold*100:.0f}% from last buy)")

                if price < last_price * (1 - self.put_threshold):
                    self.log(f"{self.time} >> SIGNAL: Consider buying protective put on {ticker} at ${price:.2f} (-{self.put_threshold*100:.0f}% from last buy)")

    def log_portfolio_summary(self):
        """Log a brief summary of the portfolio."""
        total_value = self.portfolio.total_portfolio_value
        cash = self.portfolio.cash
        self.log(f"{self.time} >> Portfolio Value: ${total_value:.2f}, Cash: ${cash:.2f}")
        for ticker in self.symbols:
            symbol = self.symbol(ticker)
            holding = self.portfolio[symbol]
            if holding.invested:
                self.log(f"   {ticker}: {holding.quantity} shares, Avg Price: ${holding.average_price:.2f}, Current: ${self.securities[symbol].price:.2f}")
