# 📊 QuantConnect Capstone Project: Buffett-Style Algo Portfolio

This repository contains the research, algorithm, and deployment workflow for my capstone project: 
a long-term **Warren Buffett-style stock portfolio** implemented through **QuantConnect's Lean engine**. 
The strategy combines fundamental investing principles with options overlays like **covered calls** and **protective puts**.

---

## 🔍 Project Overview

The algorithm manages an $8,000 virtual portfolio with the following goals:

- 📈 Focus on high-quality stocks with strong fundamentals (AAPL, MSFT, GOOGL)
- 🪙 Exposure to rare metals and energy (MP, ALB, OXY)
- 🌱 Include a renewable utility (NEE) for stability and dividend growth
- 💼 Apply options strategies (covered calls, protective puts) where appropriate
- 🧠 Follow Buffett principles: margin of safety, moats, and long-term compounding

---

## 🛠 Technologies Used

- **QuantConnect Lean CLI** – For algorithm development and deployment
- **Python** – Strategy scripting and event handling
- **Docker** – Containerized Lean environment
- **Git + GitHub** – Version control and collaboration
- **QuantConnect Paper Trading** – Live simulation with real-time data

---

## 🧪 Backtesting & Deployment

You can backtest or deploy the strategy locally using the Lean CLI:

```bash
# Must be run from the root 'quant-paper-trading' directory
lean backtest "live-trading-bot"

# For live paper trading (QuantConnect Researcher membership required)
lean live "live-trading-bot"
Be sure your config.json and live.json are configured correctly. Paper trading uses QuantConnect's built-in brokerage integration without requiring a paid third-party subscription.

🧾 Folder Structure
bash
Copy
Edit
quant-paper-trading/
├── live-trading-bot/           # Project directory
│   ├── main.py                 # Algorithm logic
│   ├── backtest-config.json    # Lean backtest config
│   ├── live.json               # Lean live paper trading config
├── .lean/                      # Lean project metadata
├── README.md                   # This file
📤 Git Workflow
bash
Copy
Edit
# From the quant-paper-trading root:
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
📬 Contact
Capstone Developer: Gabriel Pina
School: St. Petersburg College
Instructor GitHub: Prof-of-Bytes
Email: vernon.james@spcollege.edu

📘 License
This project is developed as an academic capstone. For educational use only.
