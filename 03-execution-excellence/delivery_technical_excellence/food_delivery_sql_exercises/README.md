# SQL Test - Head of Data/BA Position
*Format:* 45-minute test, 6 questions

## Guidelines
Any SQL variant OK

Focus on query structure over perfect syntax

No calculations needed—just write the SQL

Comment approach if running out of time

Not pass/fail—gauging experience level

## Schema
### Transaction Table (transaction)
- `transaction_id` (bigint)
- `restaurant_id` (bigint)
- `customer_id` (bigint)
- `transaction_date` (date)
- `transaction_value` (decimal 10,2)

### Restaurant Table (restaurant)
- `restaurant_id` (bigint)
- `restaurant_name` (varchar 100)
- `restaurant_brand` (varchar 100)
- `cuisine_type` (varchar 50)

## Questions
### Avg transaction by brand (last 7 days)
Calculate average transaction value per restaurant brand in the last 7 days.

### All restaurants + transaction count (yesterday)
List all restaurant names with transaction count from yesterday. Include restaurants with 0 transactions.

### Daily Indian vs Pizza transaction counts
Return daily counts for "Indian" and "Pizza" cuisine types in separate columns, one row per date.

### New customers in Jan 2017
Count customers whose first-ever transaction was in January 2017.

### Transactions in first 90 days per customer
Return total transactions each customer made in their first 90 days (one row per customer_id).

### Frequent spenders who went inactive
Identify customers who:
- Were frequent spenders (≥10 transactions AND >€500 total spent)
- Are now inactive (no transactions in last 12 months)

Return: `customer_id`, `total_transactions`, `total_spent`, `last_transaction_date`