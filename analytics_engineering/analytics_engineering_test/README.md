# BI Engineering Test

Please note you will need the following files to complete this test:
- **sales.csv**
- **country.csv**

All answers require you to submit the solution as a query and not a result (except questions
4 and 7). You may use any SQL syntax you are familiar with to complete the test.

Please submit your answers back to your interviewer as discussed during your interview or
outlined in the email. If you have no frame of reference, you should return the test within 2
business days. You may attach your answers within this document or in a separate file.

The last note we would like to add is, we know your time is valuable and we really appreciate you taking the time to do this test, it will greatly assist with assessing your skills and providing valuable feedback.

_When writing queries, keep the following in mind -> Write simple not complex. Readability is important. Use logical names for everything._


## 1. What are the top 10 brands by sales in the sales.csv table?

Assuming by "Sales", it is measured by `revenue`:

```sql
SELECT brand
  , SUM(revenue) AS revenue
  , COUNT(DISTINCT id_order) AS orders_ct
  , COUNT(DISTINCT id_product) AS products_ct
  , COUNT(DISTINCT id_seller) AS sellers_ct
  , COUNT(DISTINCT id_buyer) AS buyers_ct
FROM datasets_sales
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10
;

```

Numbers of orders, products, sellers and buyers are also included for additional information.




## 2. Write a query to calculate the contribution (in percentage) of each country to the total by both sales and nb of items sold. I.e. If France sold 10/100 items, then you should have 10% as the contribution for France of items sold.

```sql
WITH sales_dataset AS (
  SELECT id_seller_country
    , SUM(revenue) AS revenue
    , COUNT(DISTINCT id_product) AS products_ct
  FROM datasets_sales
  GROUP BY 1
), sales_with_country_name AS (
  SELECT s.*
    , SUM(revenue) OVER () AS revenue_all_countries
    , SUM(products_ct) OVER () AS products_ct_all_countries
    , c.country
  FROM sales_dataset s
  INNER JOIN datasets_country c ON s.id_seller_country = c.id_country
), countries_with_contribution AS (
  SELECT country
    -- Note: SAFE_DIVIDE in BigQuery would return NULL in case of "Divide by 0" error
    , COALESCE(SAFE_DIVIDE(revenue, revenue_all_countries), 0) AS revenue_contribution
    , revenue
    , revenue_all_countries
    , COALESCE(SAFE_DIVIDE(products_ct, products_ct_all_countries), 0) AS products_contribution
    , products_ct
    , products_ct_all_countries
  FROM sales_with_country_name
)
-- This root level query is solely for converting the contribution columns from FLOAT to percentage per request
SELECT country
  , CONCAT(CAST(ROUND(revenue_contribution * 100, 1) AS STRING), '%') AS revenue_contribution
  , revenue
  , revenue_all_countries
  , CONCAT(CAST(ROUND(products_contribution * 100, 1) AS STRING), '%') AS products_contribution
  , products_ct
  , products_ct_all_countries
FROM countries_with_contribution
;

```



## 3. Which two countries had the best relationship in terms of sales? Include the sales in both directions, e.g. If France sells to Germany and Germany sells to France, then you must aggregate both into a single row in your table.

```sql
WITH sales_dataset AS (
  -- The reason of using SELECT * here is Snowflake is probably not materializing CTEs, when this techique would be okay as a shorthand without having all columns scaned as long as the downstream queries are not SELECT *
  SELECT *
  FROM datasets_sales
), sales_per_countries AS (
  SELECT id_seller_country
    , id_buyer_country
    , SUM(revenue) AS revenue
  FROM sales_dataset
  GROUP BY 1,2
-- Assuming we only care about sales accross countries, and sales within the same country would be ignored
), sales_across_countries AS (
  SELECT s.*
    -- Concatenate the 2 columns for the SPLIT function later
    , CONCAT(sc.country, '&', bc.country) AS countries_mix
  FROM sales_per_countries s
  INNER JOIN datasets_country sc ON s.id_buyer = sc.id_country
  INNER JOIN datasets_country bc ON s.id_seller = bc.id_country
  WHERE id_seller_country != id_buyer_country
), sales_across_countries_array AS (
  SELECT s.*
    -- SPLIT function in BigQuery would return an ARRAY
    , SPLIT(countries_mix, '&') AS countries_arary
  FROM sales_across_countries s
), sales_across_countries_array_deduplicated_and_sorted AS (
  SELECT revenue
    -- Sorting the ARRAY by the country name and also de-duplicate the countries, so the relationship between countries would be shown in the form of an ARRAY
    , ARRAY_AGG(DISTINCT countries_arary_unnested ORDER BY countries_arary_unnested) AS countries_arary_nested
  FROM (
    SELECT s.id_seller_country
      , s.id_buyer_country
      , s.revenue
      , countries_arary_unnested
    FROM sales_across_countries_array s
    CROSS JOIN UNNEST(countries_arary) countries_arary_unnested
  )
  GROUP BY 1
)
-- Only fetch 2 countries from the sorted & deduplicated ARRAY
SELECT countries_arary_nested[0] AS country_a
  , countries_arary_nested[1] AS country_b
  , revenue
FROM sales_across_countries_array_deduplicated_and_sorted
;

```

## 4. When and why should you create a table or a view?

While conducting analysis, building data products (e.g. a Data Mart) and building dashboards, building Tables or Views would be needed.

### Analysis
In the case of analysis, one of the usual pratices would be fetching the underling data within a selected period of time, aggreate them and store in a table in a sandbox dataset/schema. This techique is espeically useful while the DWH is haivng degrading performance (e.g. taking super long to run a very simple and light query).

### Data Products
For data products, Tables/Views would be a common way to serve the data. Depends on the context, both of Table and View could be used. For example, there should only be 1 fact table of orders in a company. Assuming there is a use case from the France team, then a View with Row Level Security applied should be used to make sure France team only see France data. In this context, View would be a subset of the Table. Doing so could also save stroage cost by avoiding duplicated data in the DWH.

In addition, there could be possility to serve data with a Table/View for the consumption from another application. Yet this pratice could be a bit risky as it is building dependance on the analytical data assets from an application. A better pratice would be storing the data in S3 and let the application fetch data from there instead.

### Dashboarding
As for dashboarding, a good pratice in BI would be have a preaggerated table ready within the DWH solution. And directly fetch the table/view as it is to in the BI tool selected (e.g. Tableau, Google Data Studio, Looker etc.). Doing so, would allow the BI tool to read metadata of the table/view to further optimize the performance and cost while the dashboard is being used (e.g. If the table in BigQuery are partitioned by DATE and the dashboard has a DATE filtering only last 14 days, then the BI tool would only look at records within last 14 day in the table). On the other hand, using Custom SQL would basically kill of this kind of optimization.


## 5. What percentage of all buyers are repeat buyers represented in the second week by number of customers? (you may assume week 1 as the 1/1/2021 to 7/1/2021 and the second week as 8/1/2021 to 15/1/2021)

```sql
WITH sales_dataset AS (
  SELECT *
    -- column `date_payment` is actually not a DATE, it is a TIMESTAMP.
    , CAST(date_payment AS DATE) AS created_date
  FROM datasets_sales
  --  While comparing a TIMESTAMP value to a DATE with BETWEEN, the end date would need to be extended 1 day
  WHERE date_payment BETWEEN '2021-01-01' AND '2021-01-16'
), buyers_with_weeks AS (
  SELECT *
    -- Assuming id_buyer is unique across countires
    , ROW_NUMBER() OVER (PARITION BY id_buyer) AS buyer_week
  FROM (
    SELECT DISTINCT id_buyer
      -- Thought of using WEEK or DATE_TRUNC but it would return wrong result, hence using CASE WHEN
      , CASE
          WHEN created_date BETWEEN '2021-01-01' AND '2021-01-07'
            THEN 'Week 1'
          WHEN created_date BETWEEN '2021-01-08' AND '2021-01-15'
            THEN 'Week 2'
        END AS assumed_week
    FROM sales_dataset
  )
), weekly_buyers_agg AS (
  SELECT assumed_week
    , COUNT(DISTINCT id_buyer) AS buyers_ct
    , COUNT(DISTINCT IF(buyer_week >1, id_buyer, NULL) AS repeat_buyers_ct
  FROM buyers_with_weeks
  GROUP BY 1
)
SELECT *
  , CONCAT(CAST((COALESCE(SAFE_DIVIDE(repeat_buyers_ct, buyers_ct), 0) * 100) AS STRING), '%') AS repeat_buyers_perc
FROM weekly_buyers_agg
;

```


## 6. What was the total sales of repeat buyers in the first week compared to the second week? (answer in % increase or decrease). Note that you must first find the repeat buyers in week 2, and then use this list to calculate the sales in both weeks.


```sql
WITH sales_dataset AS (
  SELECT *
    , CAST(date_payment AS DATE) AS created_date
  FROM datasets_sales
  WHERE date_payment BETWEEN '2021-01-01' AND '2021-01-16'
), buyers_with_weeks AS (
  SELECT *
    -- Assuming id_buyer is unique across countires
    , ROW_NUMBER() OVER (buyer_week_window) AS buyer_week
    , LAG(revenue) OVER (buyer_week_window) AS revenue_from_previous_assumed_week
  FROM (
    SELECT id_buyer
      , CASE
          WHEN created_date BETWEEN '2021-01-01' AND '2021-01-07'
            THEN 'Week 1'
          WHEN created_date BETWEEN '2021-01-08' AND '2021-01-15'
            THEN 'Week 2'
        END AS assumed_week
      , SUM(revenue) AS revenue
    FROM sales_dataset
    GROUP BY 1,2
  )
  WINDOW buyer_week_window AS (
    PARTITION BY id_buyer
    ORDER BY assumed_week
  )
), assumed_week_revenue AS (
  SELECT assumed_week
    , SUM(revenue) AS total_revenue
    , SUM(revenue_from_previous_assumed_week) AS total_revenue_from_previous_assumed_week
  FROM buyers_with_weeks
  -- Only repeat buyers would have buyer week as 2
  WHERE buyer_week = 2
)
SELECT assumed_week
  , COALESCE(
        SAFE_DIVIDE(
          (total_revenue - total_revenue_from_previous_assumed_week),
          total_revenue_from_previous_assumed_week
        ),
        0
    ) AS revenue_change_perc
  , total_revenue
  , total_revenue_from_previous_assumed_week
FROM assumed_week_revenue
;

```

Additional note: the assumed week 2 (2021-01-08 to 2021-01-15) could be the actually week 1 for a buyer if they place their first order in this period of time.



## 7. The business has approached you wanting to implement a new tool that is able to combine data from several sources easily and provide basic visualisation capabilities. What would you consider in your decision making process and why?

Assuming the new tool could "combine data from several sources easily and provide basic visualisation capabilities" meaning Data Blending in BI language, the usage of it should be considered with caution.

The primary consideration would be the use cases of this new tool: are they mostly for 1-off analysis at business side?

At business/operation perspective, Data Blending provides a lot of flexbility and empower the team to conduct adhoc analysis and build dashboards themselves. Nevertheless, data visualziations coming from this context are usually performing suboptimal and hard to maintain. If it is mostly for 1-off analysis, then there shouldn't be too much of a concern at this aspect.

Another major consideration would be different version of KPIs (e.g. there should only be 1 number for how many orders from yesterday, instead of having 2-3 different numbers for the same KPI). Before empowering the business with this tool, there has to be dashboards serving as source of truth with proper documentation for the whole organization to display all North Star KPIs. If those dashboards and documentation are in place, business side could refer to them while conducting their own analysis with the new tool and make sure they calculate the right numbers.

As an addition note, Data Blending should be avoided at all cost in general BI cases and considered as a necessary evil due to performance and maintainability reasons. Having this new tool implemented would benefit business side, and it would probably introduce more tech debt to the BI side due to lower threshold of Data Blending.

To conclude, there should be a solid foundation from BI side (e.g. Data Marts and Dashboards showing North Star KPIs) before implmentation of this new tool. Having this tool would empower business side, but they should always start with the Data Marts from BI while using this new tool and fallback to raw data and even data outside of DWH. And the cost of rising tech debt at BI side should also be communicated to business side as well.


## 8. Write a statement to do the following:

a. Change the region of Australia and New Zealand to ‘OCEA’
b. Insert a new row with the following values ID_COUNTRY = 246, REGION =
‘SPACE’, COUNTRY = ‘Mars’
c. Delete the row with ID_COUNTRY = 0
Tip: It can be done with a single statement:
- https://docs.snowflake.com/en/sql-reference/sql/merge.html
- https://www.sqlshack.com/understanding-the-sql-merge-statement/



```sql
CREATE TABLE countries_to_change(
    ID_COUNTRY		INT,
    REGION		VARCHAR(50),
    COUNTRY			VARCHAR(50)
)
GO

INSERT INTO countries_to_change(ID_COUNTRY, REGION, COUNTRY) VALUES (13, 'OCEA', 'Australia')
INSERT INTO countries_to_change(ID_COUNTRY, REGION, COUNTRY) VALUES (153, 'OCEA', 'New Zealand')
INSERT INTO countries_to_change(ID_COUNTRY, REGION, COUNTRY) VALUES (246, 'SPACE', 'Mars')
INSERT INTO countries_to_change(ID_COUNTRY, REGION, COUNTRY) VALUES (0, 'UNKNOWN', 'UNKNOWN')
GO

MERGE INTO datasets_country AS country
USING countries_to_change
ON country.ID_COUNTRY = countries_to_change.ID_COUNTRY
WHEN MATCH
    AND country.ID_COUNTRY != 0
  THEN
    UPDATE SET
      country.REGION = countries_to_change.REGION

WHEN NOT MATCH
  THEN
    INSERT (ID_COUNTRY, REGION, COUNTRY)
    VALUES (countries_to_add.ID_COUNTRY, countries_to_add.REGION, countries_to_add.COUNTRY)

WHEN MATCH
    AND country.ID_COUNTRY = 0
  THEN DELETE
;

```

## 9. Write a query that is able to take all id_buyers split into odd and even groups in a JSON format. Your output should consist of two arrays inside of a json ->
```json
{
Id
_
buyers: [2,4,6...]
Is
even: true
_
},
{
Id_buyers: [1,3,5...]
Is_even: false
}
```
Hint: https://docs.snowflake.com/en/sql-reference/functions/listagg.html
https://docs.snowflake.com/en/sql-reference/functions/object_construct.html


```sql
WITH buyer_ids AS (
  SELECT DISTINCT id_buyer
  FROM datasets_sales
), buyer_ids_with_even_flag AS (
  SELECT *
    , (id_buyer % 2 = 0) AS Is_even
  FROM buyer_ids
), buyer_ids_with_even_flag_agg AS (
  SELECT Is_even
    , LISTAGG(id_buyer) AS Id_buyers
  FROM buyer_ids_with_even_flag
  GROUP BY 1
)
SELECT OBJECT_CONSTRUCT(*)
FROM buyer_ids_with_even_flag_agg
;

```


## 10. Make a list of everything you think can be improved in the following query. Note: There is a lot to be improved here, be very critical.
![q10](https://github.com/davnnis2003/vestiaire-collective-sql-test/blob/777183c6edac64e77767bcd20a84c4174d1fbf72/q10.png?raw=true)
Hint: Consider optimisation (think column-store databases), naming conventions, readability, cleanliness, etc.


### Coding Style

- Reserved Words like SELECT, FROM should always be in upper case as best pratice
- Table names and column names should not be in upper case (good thing is the query here is at least showing the intention of sticking to snake case tho), e.g. `DWH_USR.DIM_VC_USR_CUSTOMER` should be `dwh_usr.dim_vc_usr_customer` instead, `CATEGORY` should be `category` instead etc. 
- Indentation not strictly followed through: in the CTE `us_sellers`, it appears then 4 spaces are applied; Yet, the root level query is also still using 4 spaces so these 2 queries seem to be indented to the same level. It might not be a good pratice as it is not emphasising the hierarchy of these 2 queries.

### Readability

- The subquery `p` should be put as an CTE before the root level query instead.
- Duplicated code: `id_seller_country` = 223 appears at 2 places (the CTE and also root level query), should only keep 1
- ALL columns should have the alias from the table or CTE - the `date_payment` after the WHERE clause does not have an alias to specify where does it come from
- Use of comments: A better place to put it would be right before the object it is commenting on with the exact same indentation. And comments in this query could basiclly be removed as they do not add any extra useful information other than describing what the Dimension Tables are standing for - if the naming convention of those tables are not self explantory enough, the naming convention itself should be fixed or there should be a proper documentation in Confluence about all Dimension & Face tables instead of having a redundant comment here. Ultimately speaking, the best kind of code is still self-documented and 0 comment is needed :)
- Inside the CTE `us_sellers`, both of DISTINCT and GROUP BY are used - the reason of using GROUP BY is that performance would be slightly better than DISTINCT (mostly in RDBMS like PostgreSQL or Redshift, but it depends on a lot of factors actually). For better refelection of business logic, the CTE should only use DISTINCT. In addition, there is the 3rd techique to handle duplication: Windows Function, i.e.

```sql
WITH fct_vc_sls_order_product_dataset AS (
  SELECT *
    -- The columns after the PARTITION BY clause are the keys used to de-duplication, just assuming the columns of `id_product` and `id_order` to be the keys in the table
    , ROW_NUMBER() OVER (PARITITON BY id_product, id_order) AS _row_number
  FROM dwh_sls.fct_vc_sls_order_product
)
SELECT *
FROM fct_vc_sls_order_product_dataset
WHERE _row_number = 1
;

```

### Performance optimization

- `CURRENT_DATE` should be used with caution - because it would make the whole query non-determinatic (i.e. returns different results with different runs assuming the underlining data doesn't change). It could bring extra compliexity to debugging in the future.
- As a rule of thrumb, aggreation should happen before JOINs - in the root level query, it starts with the Customers Dimension table and then JOIN the fact table. It is actually an anti-pattern as the biggest table should always be at the leftest side. Instead of directly
- `dwh_sls.fct_vs_sls_order_product` is being used twice in the query - Depending if Snowflake is backed by S3 or HDFS, if it is S3 then it should be okay; But if it is HDFS, a better pratice to improve the performance of Read operation would be having a CTE first, then let the other queries depending on it, i.e.

```sql
WITH fct_vs_sls_order_product_dataset AS (
  SELECT *
  FROM `dwh_sls.fct_vs_sls_order_product`
)
-- Using * here solely for demostration purpose, in real work pratice should explicity select the needed columns ONLY
SELECT *
FROM fct_vs_sls_order_product_dataset
;

```

Also, this pratice is assuming Snowflake is not materializing CTEs whle compiling like BigQuery - if it is RDBMS like PostgreSQL or Redshift, it would have better performance to create temp tables instead of CTEs. The pricing model of BigQuery is depending on how much data being scanned, so this techique would be relevant; If it is Snowflake, then it may not be so relevant.

In addition the screenshot seems to be coming from Sublime Text or DataGrip? I would be pleased if it is DataGrip but I would be a bit cautious if it is Sublime Text ;) 

Also another side note - the longer I look the more issues I find, think if the data engineers see this would probably have a heartattack ;) Last but not least, I hope this query is coming from one of the operation personnel instead of any data talent - or else I would be concerned :) 
