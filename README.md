# Real-Time Stock Trading Engine
## Project Overview
A high-performance stock trading engine that matches buy and sell orders in real-time. The system supports up to 1,024 different ticker symbols and implements lock-free data structures to handle concurrent access from multiple threads.
## Key Components
1. Order Entry System
- Implements `addOrder()` function accepting order type (Buy/Sell), ticker symbol, quantity, and price
- Includes a simulation wrapper that generates random orders to simulate market activity

2. Order Matching Algorithm
- `matchOrder()` function pairs compatible buy and sell orders based on price compatibility (buy price ≥ lowest available sell price)
- Designed with O(n) time complexity where n is the number of orders in the book
- Implements thread-safe operations without using locks to maximize throughput

3. Technical Implementation Details
- Custom-built data structures (no imported dictionaries or maps)
- Thread-safe design to handle race conditions from multiple concurrent brokers
- Optimized for performance in high-frequency trading scenarios