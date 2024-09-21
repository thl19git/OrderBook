# OrderBook

A simple trading order book, implemented in Python. Handles both limit and market orders. Limit orders specify a max/min price, market orders do not.

The order book consists of two sides, the buy-side and the sell-side.

Each side contains a doubly linked list of order levels. Each order level contains all orders at a given price, stored in a deque.

Orders are given preference first based on price, and then based on time.