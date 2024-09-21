from collections import deque

MAX_PRICE = 100000000
MIN_PRICE = 0

class Order:
    def __init__(self, id: str, side: str, type: str, quantity: int, price: float = None) -> None:
        self.id = id
        self.side = side
        self.quantity = quantity
        if type == "MARKET":
            self.price = MIN_PRICE if side == "SELL" else MAX_PRICE
        else:
            self.price = price

    def print(self):
        print("ORDER", self.id, self.side, "QUANTITY", self.quantity, "PRICE", self.price)

class OrderLevel:
    def __init__(self) -> None:
        self.next = None
        self.previous = None
        self.orders = deque()

    @property
    def empty(self) -> bool:
        if self.orders:
            return False
        return True

    @property
    def price(self) -> float:
        if self.orders:
            return self.orders[0].price
        
    @property
    def quantity(self) -> int:
        quantity = 0
        for order in self.orders:
            quantity += order.quantity
        return quantity
        
    def add_order(self, order: Order) -> None:
        self.orders.append(order)

    def try_execute(self, order: Order) -> None:
        while self.orders and order.quantity > 0:
            passive_order = self.orders[0]
            if passive_order.quantity > order.quantity:
                # Order completely filled by passive order, passive order quantity reduced but remains positive
                self.print_execution(order, passive_order, order.quantity)
                passive_order.quantity -= order.quantity
                order.quantity = 0
            else:
                # Passive order completely filled so remove from queue, decrease order quantity by passive order quantity
                self.print_execution(order, passive_order, passive_order.quantity)
                order.quantity -= passive_order.quantity
                self.orders.popleft()

    def add_next_level(self, order_level) -> None:
        # Add an order level as the next in the list (i.e. self.next = order_level)
        next = self.next
        self.next = order_level
        order_level.next = next
        order_level.previous = self
        if next:
            next.previous = order_level

    def add_previous_level(self, order_level) -> None:
        # Add an order level as the previous in the list (i.e. self.previous = order_level)
        previous = self.previous
        self.previous = order_level
        order_level.next = self
        order_level.previous = previous
        if previous:
            previous.next = order_level

    def delete(self) -> None:
        # Remove the order level from the list
        if self.previous:
            self.previous.next = self.next
        if self.next:
            self.next.previous = self.previous

    def print_execution(self, order: Order, passive_order: Order, quantity: int) -> None:
        action, from_to = ("bought", "from") if order.side == "BUY" else ("sold", "to")
        print(f"Order", order.id, action, quantity, from_to, "order", passive_order.id, "at price", self.price)

    def print(self, reverse: bool = False) -> None:
        if reverse:
            if self.next:
                self.next.print(reverse)
            for order in reversed(self.orders):
                order.print()
        else:
            for order in self.orders:
                order.print()
            if self.next:
                self.next.print()

    def print_summary(self, reverse: bool = False) -> None:
        if reverse:
            if self.next:
                self.next.print_summary(reverse)
        print(f"${self.price} : {self.quantity}")
        if self.next and not reverse:
            self.next.print_summary()

class OrderSide:
    def __init__(self, side) -> None:
        self.order_levels : OrderLevel = None
        self.side = side

    @property
    def best_price(self) -> float:
        if self.order_levels:
            return self.order_levels.price
        
    def order_is_better_than_level(self, order: Order, order_level: OrderLevel, executing: bool = True):
        if executing:
            return (self.side == "SELL" and order.price > order_level.price) or (self.side == "BUY" and order.price < order_level.price)
        return (self.side == "SELL" and order.price < order_level.price) or (self.side == "BUY" and order.price > order_level.price)
        
    def try_execute(self, order: Order) -> None:
        order_level = self.order_levels
        while order_level and order.quantity > 0 and self.order_is_better_than_level(order, order_level):
            # Order is better than this level so try to execute at this level
            order_level.try_execute(order)
            next = order_level.next
            if order_level.empty:
                if order_level == self.order_levels:
                    self.order_levels = order_level.next
                order_level.delete()
            if order.quantity >= 0:
                # Order not completely filled, so continue to try and match
                order_level = next

    def add_order(self, order: Order) -> None:
        order_level = self.order_levels

        if not order_level:
            # No order levels exist, so create the first one
            order_level = OrderLevel()
            order_level.add_order(order)
            self.order_levels = order_level
        else:
            while True:
                if order_level.price == order.price:
                    # Order level price and order level price are equal, so add the order to the level
                    order_level.add_order(order)
                elif self.order_is_better_than_level(order, order_level, executing=False):
                    # Order price is better than order level price, so create new order level before current level
                    new_order_level = OrderLevel()
                    new_order_level.add_order(order)
                    order_level.add_previous_level(new_order_level)
                    if order_level == self.order_levels:
                        self.order_levels = new_order_level
                else:
                    # Order price is worse than order price, so move on if possible, or create new level after current level
                    if order_level.next:
                        order_level = order_level.next
                        continue
                    else:
                        new_order_level = OrderLevel()
                        new_order_level.add_order(order)
                        order_level.add_next_level(new_order_level)
                break
        self.print_order_added(order)

    def print_order_added(self, order: Order) -> None:
        print("Added", order.side, "order", order.id, "price", order.price, "quantity", order.quantity, "to the order book")

    def print(self) -> None:
        if self.order_levels:
            self.order_levels.print(reverse = self.side == "SELL")

    def print_summary(self) -> None:
        if self.order_levels:
            self.order_levels.print_summary(reverse = self.side == "SELL")

class OrderBook:
    def __init__(self) -> None:
        self.buy_side = OrderSide("BUY")
        self.sell_side = OrderSide("SELL")

    @property
    def best_ask(self) -> float:
        return self.sell_side.best_price
    
    @property
    def best_bid(self) -> float:
        return self.buy_side.best_price
    
    @property
    def spread(self) -> float:
        if self.best_ask is not None and self.best_bid is not None:
            return self.best_ask - self.best_bid
        
    @property
    def mid(self) -> float:
        if self.best_ask is not None and self.best_bid is not None:
            return (self.best_ask + self.best_bid) / 2

    def add_order(self, order: Order) -> None:
        if order.side == "BUY":
            self.sell_side.try_execute(order)
            if order.quantity > 0:
                self.buy_side.add_order(order)
        else:
            self.buy_side.try_execute(order)
            if order.quantity > 0:
                self.sell_side.add_order(order)
    
    def print(self):
        print("#"*100)
        print("Sell-side orders:")
        self.sell_side.print()
        print("#"*100)
        print("Buy-side orders:")
        self.buy_side.print()
        print("#"*100)
        
    def print_summary(self):
        print("#"*100)
        print("Sell-side:")
        self.sell_side.print_summary()
        print("#"*100)
        print("Buy-side:")
        self.buy_side.print_summary()
        print("#"*100)
        
order_book = OrderBook()

order_book.add_order(Order("001", "SELL", "LIMIT", 500, 103))
order_book.add_order(Order("002", "SELL", "LIMIT", 800, 105))
order_book.add_order(Order("003", "SELL", "LIMIT", 600, 104))
order_book.add_order(Order("004", "BUY", "LIMIT", 1000, 110))
order_book.add_order(Order("005", "BUY", "LIMIT", 1000, 98))
order_book.add_order(Order("006", "BUY", "LIMIT", 1000, 98))
order_book.add_order(Order("007", "BUY", "LIMIT", 1000, 92))
order_book.add_order(Order("008", "BUY", "LIMIT", 1000, 97))
order_book.add_order(Order("009", "BUY", "LIMIT", 1000, 100))

order_book.print_summary()

