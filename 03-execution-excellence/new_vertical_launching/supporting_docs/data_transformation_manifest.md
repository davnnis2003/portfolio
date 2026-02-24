# **Data Transformation Manifest**

Following you can find a documentation called the Data transformation manifest. It will be used as a guideline for the process of data transformation in dbt, describing the layer structure & functions, table & column naming conventions and other rules to be followed within the process.

###### **Sources & inspiration**

* [dbt style guide](https://docs.getdbt.com/guides/best-practices/how-we-style/0-how-we-style-our-dbt-projects)  
* [dbt modular data modeling](https://www.getdbt.com/analytics-engineering/modular-data-modeling-technique/)  
* [dbt model structure best practices](https://towardsdatascience.com/dbt-models-structure-c31c8977b5fc)

# **A. Layer Concepts & Functions**

## **A.1. Overview of Layers**

### **Layer structure overview**

#### **Raw layer**

* Format  
* Rename  
* Clean

#### **Staging layer**

* Build objects, concepts  
* One off node reduction  
* Clean joins (intra-source joins)

#### **Base layer**

* Join concepts  
* Build business logics

#### **Marts**

* Build OBT  
* Core \- cross-department objects  
* Marts \- departments specific objects

## **A.2. Detailed Layer Functions**

### **Raw layer**

**1\. Format:**

* **Cast data type**  
* **Rename**  
  * Rename columns to align with known business terms  
  * Do not repeat table objects in column names  
    * exception: key \-\> contract\_key, payment\_key  
* **Convert**  
  * Cents \-\> Currency  
  * UTC time \-\> Timezone  
* **Categorize**  
  * Use conditional logic to group values  
    * case when category in (9, 10, 11) then 'category_a' else 'category_b'  
  * Translate integer values to string  
    * status \= active instead of status \= 7

**2\. Clean:**

* Remove duplicates  
* Do not use filters to exclude further not relevant transactions (eg. deleted claims, etc.)

### **Staging layer**

* Stage concepts  
* Use clean joins (intra-source joins)  
* Enrich objects with related data from other tables  
* Do not reference source tables (only raw layer tables)  
* Join dimensions with no/low or same change frequency as the main table object  
* Do not join transactional/event data to dimensional tables  
* Exclude not relevant transactions (e.g deleted contracts, etc.)

### **Base layer**

* Build business logics  
* Joining staging models based on business concern  
* Only reference staging layer tables

### **Marts**

* Combine base layer tables to wide tables (One-Big-Table)  
* Create both aggregated and not aggregated tables  
* Group models by business units  
  * Core \- all cross department objects  
  * Sales  
  * Marketing

# **B. Naming Convention Table & Column naming**

## **B.1. Specific Rules to Layers**

### **Raw layer**

* Source oriented naming  
* Output naming format:

`raw_[source]__[type]_[entity]s`

`raw_internal application 2__fct_transactions`  
`raw_internal application 1__dim_customers`

## **Staging layer**

* Source oriented naming  
* Output naming format:

`stg_[source]__[type]_[entity]s`

`stg_internal application 1__dim_contracts`

## **Base layer**

* Business oriented naming  
* Output naming format:

`base_[business_logic]__[type]_[entities]`

`base_sales__fct_calls`  
`base_core__dim_contracts`   
`base_sales__dim_contracts`  
`base_marketing__dim_contract_attribution`

## **Marts**

* Business oriented naming  
* Output naming format:

`[business_logic].[entities]`

`core.contracts`

Aggregated tables:

`[business_logic].[agg]_[entities]`

`sales.agg_acquisition_goals`

## 

## **B.2. General Rules**

* Use American English  
* For column and table naming: use snake case (underscores to separate lower case words)  
* For values:  
  * Concrete (product, campaign, etc.) names, codes, German word versions: use original versions  
  * All other use cases: use lower case and spaces to separate words  
* Use plural forms

### **B.2.1. Table naming**

Goal \- from the table name, it should be clearly understandable:

* Which layer it belongs to  
* What is the table type  
* What is the table content/purpose

**Raw & Staging layers** \-\> source oriented naming

**Base & Mart layers** \-\> business oriented naming

**Main table types:**

**1\. Fact table** \-\> fct \-\> A fact table typically contain a large number of numeric values representing measurable events or business transactions, hence is narrow table with transactions, rule of thumb: more numbers than strings, e.g.: fct\_calls

**2\. Dimensional table** \-\> dim \-\> A dimensional table contains more string values compared to numeric values and usually have attributes that do not change frequently. It is used to providing additional details and dimensions for analyzing data in conjunction with fact tables, e.g.: dim\_policies, dim\_customers

**3\. One-big table** \-\> no prefix. in Marts layer. Fact and dimensional tables are combined into a single wide table per object. The relevant attributes from both types of tables are merged into a one-big table.

**4\. Aggregated table** An aggregated table summarizes data at a higher level by aggregating values from multiple source tables. It contains aggregated metrics, such as sums, averages, or counts and so on. This table typically summarizes data (some measures) across any number of dimensions.

**5\. Historized Table** A historized table is used to store historical data and track changes over time. It is commonly used for tracking audits of claims, payments and so on.

**6\. Transactional Table** A transactional table stores transactions or events as they occur over time.

### **B.2.2. Column naming**

Rules \- addition to the previously mentioned basic principles for tables & columns:

**1\. Use abbreviations**, where it makes sense

* avg, not average; doc, not document;  
* BUT do not oversimplify \-\> current\_contract\_status better than current\_cs

**2\. Do not use postpositive adjectives** (modifiers placed after the noun)

* cancelled\_gwp, **not** gwp\_cancelled;  
* closed\_leads, **not** leads\_closed

**3\. Use units of measurement**

* currency:  
  * if currency column **not present** in table: total\_costs\_eur  
  * if currency column **present** in table: total\_costs  
* count: count\_contracts  
* time / duration:  
  * avg\_handling\_time\_**hrs**  
  * wait\_time\_**sec**  
  * call\_duration\_**min**

**4\. Do not repeat table objects in column names (only use foreign objects)**

* contracts table \-\> start\_date, **not** contract\_start\_date  
* contracts table \-\> lead\_channel

**5\. Use standardized namings for agents**

* do not use term user, use agent & employee  
* variants:

**agent\_id / employee\_id**

* Showing the source service id (internal application 2, zendesk, etc…)  
* Example: 362505167494

**agent / employee**

* Showing the company user name of an agent / employee  
* Example: ktestimaus

**agent\_name / employee\_name**

* Showing the full name of an agent / employee  
* Example: Klaus Testimaus

**agent\_hash / employee\_hash**

* Showing the hashed value of the company user name  
* Example: ba9fe26625e0fcc05df74afe3ht03dc9

**6\. Date & Time fields**

**Date fields**

* Preferred naming \[event\]\_date \-\> created\_date  
* Format: yyyy-mm-dd  
* Other possible suffixes: \_from, \_until

**Week date fields**

* Preferred naming \[event\]\_week \-\> created\_week  
* Format: yyyy-ww

**Month date fields**

* Preferred naming \[event\]\_month \-\> created\_month  
* Format: yyyy-mm

**Timestamp fields**

* Preferred naming \[event\]\_at \-\> created\_at  
* Format: yyyy-mm-dd hh:mi:ss  
* Other possible suffixes: \_timestamp, \_start, \_end

**7\. Further field definitions**

**Flag fields**

* Contains values 0 for false and 1 for true (NULL values should not occur)  
* Preferred naming suffix: **\_flag** \-\> sales\_contract\_flag

**Boolean fields**

* Contains boolean values FALSE & TRUE  
* Preferred naming prefix or use of: **has** / **is** \-\> has\_trial\_month / is\_deleted

### **B.2.3. Examples of Field Name Creation**

**Measures**

`[agg]_[measure]_[unit]`   
  `->` `total_gwp_eur`  
  `->` `avg_net_gwp_eur`

`[agg]_[measure_description]_[measure]_[unit]`  
  `->` `total_online_mta_net_gwp_eur`

`[agg]_[state_condition]_[measure_description]_[measure]_[unit]`  
  `->` `total_cancelled_online_mta_net_gwp_eur`

`[agg]_[time_condition]_[state_condition(s)]_[measure_description]_[measure]_[unit]`  
  `->` `total_daily_cancelled_online_mta_net_gwp_eur`

`[agg]_[time_condition]_[state_condition(s)]_[measure_description]_[measure]_[target` `/` `blank` `if` `actual` `number]_[unit]`  
  `->` `total_daily_cancelled_online_mta_net_gwp_target_eur`

**Dimensions**

* If table name same as object type then do not repeat table name in column names

* In contracts table:

`[dim_name]`  
 `->` `start_date`  
 `->` `id`  
   
`[object_type]_[dim_name]`  
 `->` `lead_channel`

# **C. dbt Workflow Guidelines**

Inspiration in dbt docs:

* SQL style inspiration: [dbt SQL style guide](https://docs.getdbt.com/guides/best-practices/how-we-style/2-how-we-style-our-sql)  
* YAML style inspiration: [dbt YAML style guide](https://docs.getdbt.com/guides/best-practices/how-we-style/5-how-we-style-our-yaml)

## **C.1. Modelling**

* Create separate yml configuration file for each model  
* Use the same name for model and yml file  
* Primarily use CTEs as shown in this [example](https://docs.getdbt.com/guides/best-practices/how-we-style/2-how-we-style-our-sql#example-sql-1) or in stg_internal application 1_dim_contract_insured_persons.sql  
* Model configurations (tests, tags, contracts, etc.) should be placed within the yml properties file  
  * Exception: **Indexes** & **Incremental** configurations can only be placed in the config block within the model file

## **C.2. Testing**

* Each model should have at least the basic **unique** & **not\_null** tests set up

  * Example:  
    * primary key tests:  
      * unique  
      * not\_null  
    * created timestamp tests:  
      * not\_null  
* For models in staging and downstream layers also use tests from [dbt-utils](https://github.com/dbt-labs/dbt-utils#readme) & [dbt-expectations](https://github.com/calogica/dbt-expectations/tree/0.8.2/#readme) packages

## 

## **C.3. Documentation**

* Every object of the data model should have a description incl. models, columns, seeds, sources, snapshots, etc.

