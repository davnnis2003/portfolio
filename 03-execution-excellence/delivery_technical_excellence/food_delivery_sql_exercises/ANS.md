# SQL Test - Head of Data & BA

## Jimmy Pang

# Questions

## 1. Write a query that calculates the average transaction value for each** restaurant brand** in the last 7 days.

```sql
WITH transactions_per_restaurant_agg AS (  
 SELECT restaurant_id  
   , SUM(transaction_value) AS transaction_value_sum  
   , COUNT(*) AS nb_transactions  
 FROM transaction  
 WHERE transaction_date >= CURRENT_DATE - INTERVAL '7 days'  
 GROUP BY 1  
)  
SELECT restaurant.restaurant_brand  
 , SUM(transactions_per_restaurant_agg.transaction_value_sum) AS transaction_value_sum  
 , SUM(transactions_per_restaurant_agg.nb_transactions) AS nb_transactions  
 , transaction_value_sum/nb_transactions AS avg_transaction_value  
FROM transactions_per_restaurant_agg  
INNER JOIN restaurant ON transactions_per_restaurant_agg.restaurant_id = restaurant.restaurant_id  
GROUP BY 1
```

The calculation of the Average is actually SUM / COUNT, and it is done this way for the DWH performance consideration and also for the query's extensibility (e.g., it would be very easy to extend the timeframe to last 30 days or to add the number of Restaurants per brand, etc. It is also because the Dimension of `restaurant_brand` only exists in the Dimension table `restaurant.`

* We are not focusing too much on the syntax here (say, the reference of the `transaction_value_sum` in the same query would work in Snowflake but may not work in other SQL dialects).

##  2. Write a query that returns a list of all** restaurant names** in the database, along with the number of transactions they processed yesterday. The result set should include** all restaurants** regardless of whether or not they had a transaction.

```sql
WITH transactions_per_restaurant_agg AS (  
 SELECT restaurant_id  
   , SUM(transaction_value) AS transaction_value_sum  
   , COUNT(*) AS nb_transactions  
 FROM transaction  
 WHERE transaction_date >= CURRENT_DATE - INTERVAL '1 days'  
 GROUP BY 1  
)  
SELECT restaurant.restaurant_name  
 , COALESCE(transactions_per_restaurant_agg.nb_transactions, 0) AS nb_transactions  
FROM restaurant  
LEFT JOIN transactions_per_restaurant_agg ON restaurant.restaurant_id = transactions_per_restaurant_agg.restaurant_id
```

There's not much note to add here, it should be straightforward.

* It may be helpful to sort the list with ORDER BY, depending on the finetuning requirement in the business case, stakeholder preference, etc.

## 3. Write a query that returns a daily count of the number of "Indian" cuisine type transactions and the number of "Pizza" cuisine type transactions. Your result set should have one row per transaction date, and the cuisine transaction counts should be presented in** separate columns.**

```sql
SELECT transaction.transaction_date  
 , COUNT_IF(restaurant.cuisine_type = 'Indian') AS nb_transactions_cuisine_indian  
 , COUNT_IF(restaurant.cuisine_type = 'Pizza') AS nb_transactions_cuisine_pizza  
FROM transaction  
INNER JOIN restaurant ON transaction.restaurant_id = restaurant.restaurant_id  
GROUP BY 1  
ORDER BY 1 DESC
```

* I always prefer `COUNT_IF` instead of `SUM(CASE WHEN condition THEN 1 END)` - as writing the query this way is shorter. Less is more.

Alternatively, it can be written as:  
```sql
SELECT transaction.transaction_date  
 , COUNT(CASE WHEN restaurant.cuisine_type = 'Indian' THEN 1 END) AS nb_transactions_cuisine_indian  
 , COUNT(CASE WHEN restaurant.cuisine_type = 'Pizza' THEN 1 END) AS nb_transactions_cuisine_pizza  
FROM transaction  
INNER JOIN restaurant ON transaction.restaurant_id = restaurant.restaurant_id  
GROUP BY 1  
ORDER BY 1 DESC
```

It is just not my preferred style to write it.

##  4. Write a query that returns the total number of customers whose first ever transaction was in January 2017.

```sql
WITH customer_with_first_transation_date AS (  
 SELECT customer_id  
   , MIN(transaction_date) AS first_transaction_date  
 FROM transaction  
 GROUP BY 1  
)     
SELECT COUNT(DISTINCT customer_id)  
FROM customer_with_first_transation_date  
WHERE first_transaction_date BETWEEN '2017-01-01' AND '2017-01-31'
```

For better readability, it is better to use CTE (Common Table Expression) instead of subquery, as human readers often start reading from top to bottom.

Alternatively, if using CTE:  
```sql
SELECT COUNT(DISTINCT customer_id)  
FROM (  
 SELECT customer_id  
   , MIN(transaction_date) AS first_transaction_date  
 FROM transaction  
 GROUP BY 1  
) customer_with_first_transation_date  
WHERE first_transaction_date BETWEEN '2017-01-01' AND '2017-01-31'
```

The reading direction would confuse the query's reader as the reader would be required to read back and forth the query (especially in case of longer queries). Queries and code are usually written once and read more than 10 times. It is always better to opt for better reading than better writing.

## 5. Write a query that returns the total number of transactions that a customer makes in their first 90 days. Your result set should have one row per customer_id.

```sql
WITH customer_with_first_transation_date AS (  
 SELECT customer_id  
   , MIN(transaction_date) AS first_transaction_date  
 FROM transaction  
 GROUP BY 1  
)  
SELECT transaction.customer_id  
 , COUNT(transaction.transaction_id) AS nb_transactions  
FROM transaction  
INNER JOIN customer_with_first_transation_date ON transaction.customer_id = customer_with_first_transation_date.customer_id  
WHERE transaction.transaction_date <= customer_with_first_transation_date.first_transaction_date + INTERVAL '90 days'  
GROUP BY 1  
ORDER BY 2 DESC
```

* Similar case as above, using CTE here for better readability   
* Also, sorting the output of the query with `nb_transactions` descendingly so that the biggest spender will be on the top and the most significant opportunities will be there for the stakeholders

## 6. Write a query that identifies customers who:

###  a. Are frequent spenders (defined as customers who made at least 10 transactions and spent over €500 in total) in their whole order history.

### b. Are inactive customers (defined as no transactions in the last 12 months).

### c. Were frequent spenders and are inactive now.

The result should include the customer_id, total_transactions, total_spent (for the period when they were active), and the last date they made a transaction.

```sql
WITH customer_summary AS (  
 SELECT customer_id  
   , COUNT(transaction_id) AS total_transactions  
   , SUM(transaction_value) AS total_spent  
   , MAX(transaction_date) AS lastest_transaction_date  
 FROM transaction  
 GROUP BY 1  
)  
SELECT customer_id  
 , total_transactions  
 , total_spent  
 , lastest_transaction_date  
 , (total_transactions >= 10  
     AND total_spent > 500  
   ) AS is_frequent_spender  
 , (lastest_transaction_date < CURRENT_DATE - INTERVAL '12 months' ) AS is_inactive_customer  
FROM customer_summary  
ORDER BY lastest_transaction_date DESC
```

* Using BOOLEAN columns ( `is_frequent_spender` and `is_active_customer` ) for better readability   
* Those 2 columns can be refactored into STRING values to contain more possible values for extended business requests, e.g.  
  * `CASE WHEN total_transactions >= 10 AND total_spent > 500 THEN 'Frequent Spender' ELSE 'Regular' END AS customer_type,`  
  * `CASE WHEN last_transaction < CURRENT_DATE - INTERVAL '12 months' THEN 'Inactive' ELSE 'Active' END AS activity_status`

# Appendix

* I use very explicit names for CTEs and aliases to improve readability. Names like `a` or `t` alias don’t help readers to understand the queries as it introduces guessing games (not everyone could instantly understand `t` stands for “transaction”, for example)   
* The `ROUND` function is avoided as it may unnecessarily sacrifice the precision of FLOATs. Truncating the long tail in dashboards like Tableau is generally better.    
  * This is to preserve precision for different use cases of the same query, e.g., Machine Learning, and Finance reporting.  
  * By doing so, we could reuse the same queries for different use cases instead of writing new queries every time new business requests arrive.  
* My preferred coding styles in SQL are:  
  * 2 spaces indentation  
  * Reserved words being upper case (it is handy while SQL code is mixed with Python code)  
  * Lead commas (as against trail commas)  
  * Explicit over Implicit (e.g. using `INNER JOIN` instead of just `JOIN`  
* ChatGPT is used for this assignment. Generally, the whole PDF file is passed to the AI, and I validate the generated outcome. This ensures the speed and quality of the outcome—convo for reference [here](https://chatgpt.com/share/67a7644c-917c-8010-b113-32f6491a57d2).
