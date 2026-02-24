# Data Ninja SQL Test

## Tables

### test_orders

| customer_id | purchase_date | purchase_revenue |
| ----------- | ------------- | ---------------- |
| 1           | 2015-01-01 14:32:51 | 25.34 |
| 2           | 2015-01-02 12:14:51 | 34.34 |
| 3           | 2015-01-02 18:08:21 | 37.15 |
| 2           | 2015-03-02 23:42:21 | 47.24 |
| 2           | 2015-04-02 23:42:21 | 54.12 |
| 3           | 2015-07-03 22:07:11 | 65.21 |
| 1           | 2015-09-03 21:02:41 | 74.60 |
| 3           | 2015-10-03 05:15:24 | 11.30 |
| 2           | 2015-10-03 07:11:56 | 22.45 |

### test_order_details

| customer_id | order_id | purchase_timestamp | number_items | purchase_price | item_status |
| ----------- | -------- | ------------------ | ------------ | -------------- | ----------- |
| 1           | 1        | 2015-01-01 14:32:51 | 2            | 4.35           | returned    |
| 1           | 1        | 2015-01-01 14:32:51 | 3            | 8.446666667    | sold        |
| 2           | 1        | 2015-01-02 12:14:51 | 1            | 24             | sold        |
| 2           | 1        | 2015-01-02 12:14:51 | 2            | 5.17           | sold        |
| 3           | 1        | 2015-01-02 18:08:21 | 3            | 10             | sold        |
| 3           | 1        | 2015-01-02 18:08:21 | 1            | 7.15           | sold        |
| 2           | 2        | 2015-03-02 23:42:21 | 2            | 20             | sold        |
| 2           | 2        | 2015-03-02 23:42:21 | 1            | 7.24           | returned    |
| 2           | 2        | 2015-03-02 23:42:21 | 1            | 7.24           | sold        |
| 2           | 3        | 2015-04-02 23:42:21 | 3            | 18.04          | sold        |
| 3           | 2        | 2015-07-03 22:07:11 | 2            | 20             | sold        |
| 3           | 2        | 2015-07-03 22:07:11 | 1            | 25.21          | sold        |
| 3           | 2        | 2015-07-03 22:07:11 | 4            | 17.21          | returned    |
| 1           | 2        | 2015-09-03 21:02:41 | 3            | 10.2           | sold        |
| 1           | 2        | 2015-09-03 21:02:41 | 2            | 22             | sold        |
| 1           | 2        | 2015-09-03 21:02:41 | 1            | 15             | returned    |
| 3           | 3        | 2015-10-03 05:15:24 | 1            | 11.3           | sold        |
| 2           | 4        | 2015-10-03 07:11:56 | 1            | 22.45          | sold        |

## Questions

Q1: Calculate first date (YYYY-MM-DD) when customer's cumulative purchase_revenue reaches ≥100€
Output: date (DATE), customer_id (INTEGER)

Q2: Return only customers with cumulative purchases >100€
Output: customer_id (INTEGER)

Q3: Calculate days between first/last purchase + revenue per day for each customer
Output: customer_id (INTEGER), days_between_last_and_first_purchase (INTEGER), revenue_per_day (FLOAT)

Q4: Verify test_orders.purchase_revenue = SUM(number_items × purchase_price) for sold items. Output difference if mismatch
Output: customer_id (INTEGER), order_id (INTEGER), verified (BOOLEAN), difference (FLOAT, NULL if match)

Q5: Calculate per customer: extra revenue if no returns, original revenue, new revenue (no returns), % increase
Output: customer_id (INTEGER), extra_revenue (FLOAT), original_revenue (FLOAT), new_revenue (FLOAT), percentage_increase (FLOAT)

Q6: Based on Q5, which customer deserves most/least attention to reduce returns and why?

Q7: Based on Q4, how to improve test_orders to simplify JOIN with test_order_details?