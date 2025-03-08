import time
import threading
import ctypes
import random

class AtomicInteger:
    """Lock-free atomic integer for thread-safe quantity updates."""
    
    def __init__(self, value=0):
        self.value = ctypes.c_int(value)

    def add(self, delta):
        """Atomically adds `delta` to the value."""
        
        while True:
            current = self.value.value
            new_value = current + delta
            if ctypes.c_int(current).value == current:  # Simulating atomic compare-and-swap
                self.value.value = new_value
                return new_value

    def subtract(self, delta):
        """Atomically subtracts `delta` from the value."""
        return self.add(-delta)

    def get(self):
        """Returns the current value."""
        return self.value.value
    
class Order:
    """Represents a Buy or Sell order in the stock market."""
    
    def __init__(self, order_type, ticker, quantity, price):
        self.order_type = order_type  # "Buy" or "Sell"
        self.ticker = ticker
        self.quantity = AtomicInteger(quantity) # Atomic variable
        self.price = price  
        self.next = None

class OrderBook:
    """Manages Buy and Sell orders using sorted linked lists."""

    def __init__(self):
        self.buy_orders = [None] * 1024  # Aaray of linked-list with descending price (Order with highest budget comes first)
        self.sell_orders = [None] * 1024  # Aaray of linked-list with ascending price (Order with lowest price comes first)

    def add_order(self, order_type, ticker, quantity, price):
        """
        Call matching function before adding a new order.
        """
        
        new_order = Order(order_type, ticker, quantity, price)
          
        # Assign the correct order list
        order_list = self.buy_orders if order_type == "Buy" else self.sell_orders
           
        # Try to match before adding new orders to the book
        executed_trades = self.match_orders(new_order)
        
        # If there's remaining quantity, insert into the order book
        if new_order.quantity.get() > 0:
            self._insert_order(order_list, ticker, new_order)

        return executed_trades  # Return executed trades for logging
    
    def _insert_order(self, order_list, ticker, new_order):
        """
        Adds an order to the order book while maintaining sorted order.
        """
        
        # Insert into linked list
        head = order_list[ticker]
        if head is None:
            # No orders yet, so new order becomes the head
            order_list[ticker] = new_order 
        elif (new_order.order_type == "Buy" and head.price <= new_order.price) or (new_order.order_type == "Sell" and head.price >= new_order.price):
            # New order is with highest priority, so it becomes the new head
            new_order.next = head
            order_list[ticker] = new_order 
        else:
            # Traverse the list to find the correct position
            current = head
            while current.next and ((new_order.order_type == "Buy" and current.next.price > new_order.price) or (new_order.order_type == "Sell" and current.next.price < new_order.price)):
                current = current.next
            new_order.next = current.next
            current.next = new_order
        

    def match_orders(self, new_order):
        """
        Matches Buy and Sell orders for a certain ticker where Buy price >= lowest Sell price.
        If matched, execute trade and adjust remaining quantity.
        """
        
        executed_trades = []
        
        if new_order.order_type == "Buy":
            sell_orders = self.sell_orders[new_order.ticker]
            while sell_orders and sell_orders.price <= new_order.price:
                matched_quantity = min(new_order.quantity.get(), sell_orders.quantity.get())
                executed_trades.append((new_order.price, matched_quantity, new_order.ticker))  # Log execution
                
                # Adjust quantities using atomic operations
                if sell_orders.quantity.subtract(matched_quantity) == 0:
                    self.sell_orders[new_order.ticker] = sell_orders.next  # Remove matched sell order
                if new_order.quantity.subtract(matched_quantity) == 0:
                    return executed_trades  # Fully matched, return trades
                
                # Check the next available Sell order
                sell_orders = self.sell_orders[new_order.ticker]
        else:
            buy_orders = self.buy_orders[new_order.ticker]
            while buy_orders and buy_orders.price >= new_order.price:
                matched_quantity = min(new_order.quantity, buy_orders.quantity)
                executed_trades.append((new_order.price, matched_quantity, new_order.ticker))
                
                # Adjust quantities using atomic operations
                if buy_orders.quantity.subtract(matched_quantity) == 0:
                    self.buy_orders[new_order.ticker] = buy_orders.next
                if new_order.quantity.subtract(matched_quantity) == 0:
                    return executed_trades
                
                # Check the next available Buy order
                buy_orders = self.buy_orders[new_order.ticker]
                
        # When no more matches was found, return so _insert_order() can perform the adding of the new order
        return executed_trades
        

    def print_orders(self):
        """Print orders for debugging."""
        
        print("\n--- BUY ORDERS ---")
        for i in range(1024):
            current = self.buy_orders[i]
            while current:
                print(f"Ticker {i}: BUY {current.quantity.get()} shares at ${current.price}")
                current = current.next

        print("\n--- SELL ORDERS ---")
        for i in range(1024):
            current = self.sell_orders[i]
            while current:
                print(f"Ticker {i}: SELL {current.quantity.get()} shares at ${current.price}")
                current = current.next

def generate_random_order():
    """Generate random order details."""
    
    order_type = random.choice(["Buy", "Sell"]) 
    ticker_index = random.randint(0, 1023)  # Get random ticker index 0~1023
    quantity = random.randint(10, 500)  # Random quantity (10 to 500 shares)
    price = round(random.uniform(100, 150), 2)  # Random price between $100 and $150

    return order_type, ticker_index, quantity, price

def simulate_trading(order_book):
    """
    Wrapper function to generate random stock transactions.
    It will add Buy/Sell orders and attempt to match them.
    """
    
    for _ in range(50):  # Simulate 50 random orders
        order_type, ticker_index, quantity, price = generate_random_order()

        print(f"\nAdding {order_type} Order: {quantity} shares of Ticker {ticker_index} at ${price}.")
        executed_trades = order_book.add_order(order_type, ticker_index, quantity, price)
        
        # Log executed trades
        for price, qty, ticker in executed_trades:
            print(f"Trade Executed: {qty} shares of Ticker {ticker} at ${price}")

        order_book.print_orders()


# Run the trading engine
if __name__ == "__main__":
    order_book = OrderBook()

    # Multi-threaded simulation for concurrency testing
    threads = []
    for _ in range(3):  # Simulate 3 stockbrokers adding orders concurrently
        t = threading.Thread(target=simulate_trading, args=(order_book,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()  # Wait for all threads to complete

    print("\nFinal Matching Completed")
