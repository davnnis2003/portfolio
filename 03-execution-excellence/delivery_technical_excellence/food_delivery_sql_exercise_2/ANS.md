Data Ninja SQL Test - All Solutions

```sql
-- Q1: First date cumulative revenue >=100€ per customer
-- Output: date (DATE), customer_id (INT)
WITH cum_rev AS (
  SELECT 
    customer_id,
    DATE(purchase_date) AS purchase_date,
    purchase_revenue,
    SUM(purchase_revenue) OVER (PARTITION BY customer_id ORDER BY purchase_date ROWS UNBOUNDED PRECEDING) AS cum_purchase_revenue
  FROM test_orders
)
SELECT 
  MIN(purchase_date) AS date,
  customer_id
FROM cum_rev
WHERE cum_purchase_revenue >= 100
GROUP BY customer_id
ORDER BY date;
```

```sql
-- Q2: Customers with total purchases >100€
-- Output: customer_id (INT)
WITH totals AS (
  SELECT 
    customer_id,
    SUM(purchase_revenue) AS total_revenue
  FROM test_orders
  GROUP BY customer_id
  HAVING SUM(purchase_revenue) > 100
)
SELECT customer_id
FROM totals
ORDER BY total_revenue DESC;
```

```sql
-- Q3: Days between first/last purchase + revenue/day
-- Output: customer_id (INT), days_between (INT), revenue_per_day (FLOAT)
WITH lifevalue AS (
  SELECT 
    customer_id,
    MIN(purchase_date) AS min_purchase_date,
    MAX(purchase_date) AS max_purchase_date,
    SUM(purchase_revenue) AS total_revenue
  FROM test_orders
  GROUP BY customer_id
)
SELECT 
  customer_id,
  EXTRACT(DAY FROM (max_purchase_date - min_purchase_date)) AS days_between_last_and_first_purchase,
  total_revenue / EXTRACT(DAY FROM (max_purchase_date - min_purchase_date))::FLOAT AS revenue_per_day
FROM lifevalue
ORDER BY revenue_per_day DESC;
```

```sql
-- Q4: Verify revenue = SUM(sold items num_items * price)
-- Output: customer_id (INT), order_id (INT), verified (BOOL), difference (FLOAT NULL if match)
WITH sold_sum AS (
  SELECT 
    customer_id,
    order_id,
    SUM(number_items * purchase_price) AS calc_revenue
  FROM test_order_details
  WHERE item_status = 'sold'
  GROUP BY customer_id, order_id
)
SELECT 
  to.customer_id,
  to.order_id,
  (to.purchase_revenue = ss.calc_revenue) AS verified,
  CASE 
    WHEN to.purchase_revenue = ss.calc_revenue THEN NULL 
    ELSE ss.calc_revenue - to.purchase_revenue 
  END AS difference
FROM test_orders to
LEFT JOIN sold_sum ss ON to.customer_id = ss.customer_id AND to.order_id = ss.order_id;
```

```sql
-- Q5: Extra revenue if no returns, original, new, % increase
-- Output: customer_id (INT), extra (FLOAT), original (FLOAT), new (FLOAT), % (FLOAT)
WITH rev_calc AS (
  SELECT 
    customer_id,
    SUM(number_items * purchase_price) FILTER (WHERE item_status = 'returned') AS extra_revenue,
    SUM(number_items * purchase_price) FILTER (WHERE item_status = 'sold') AS original_revenue,
    SUM(number_items * purchase_price) AS new_revenue
  FROM test_order_details
  GROUP BY customer_id
)
SELECT 
  customer_id,
  extra_revenue,
  original_revenue,
  new_revenue,
  (extra_revenue / original_revenue)::FLOAT AS percentage_increase
FROM rev_calc;
```

Q6:
In terms of reducing the number of returning items, customer 3 & 2 would be my main focus.

1, Customer_id 3 worth paying the most attention
Customer_id 3 has the highest amount of returned purchase revenue (Euro 68.84) and the highest number of returning items (4). According to this customer's spending pattern, it is reasonable to predict he/she will make more decently priced products if he/she have a better shopping experience.

2, Customer_id 2 worth paying the least attention
Among 3 customers, Customer_id 2 has the lowest number of returned items (1) and price of the returned item is the cheapest (Euro 7.24) as well. It would be more cost-efficient to spend time and resource on retaining other customers who are likely to spend more.

Q7:
The key here is adding Primary Keys and Foreign Keys to both of the tables.

Table `test_orders`
For `test_orders`, it is better to add 1 more column: `order_id`. It would be ideal if we can make this new `order_id` column as the Primary Key of the `test_orders` Table, and a Foreign Key for `test_orer_details` table

Table `test_orders_details`
Meanwhile, it would also help if we can have an extra column named `order_details_id` to be the Primary Key of the `test_order_details` Table and convert the original `order_id` column as a Foreign Key to the `test_orders` Table.

With both of the Primary Keys and Foreign Keys properly set up, joining work afterward would be much simpler and easier.