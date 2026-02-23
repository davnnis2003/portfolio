# Case Study Spec

# Staff Data Analyst - Case Study

## Jimmy Pang

This doc has two parts: 

1. Sections 0–7 with the proposed MVP, architecture, and business logic;  
2. Appendices with detailed exploration notes in another tab. The main sections are enough to evaluate the solution; the appendices show extra depth behind the solution.

# 0. Executive Summary

**Problem (what’s broken)**

* No trusted view of which campaigns/channels actually create customers, not just leads.  
* Data quality issues (UTMs, campaign naming, campaign_metadata coverage) block reliable attribution and CAC.  
* No shared marketing performance mart or dashboard, so Marketing and Sales argue without a common source of truth.

**Key findings from the data**

* ~€260k ad spend over 2 months → 830 leads → 352 opportunities → 47 customers: CAC is high, with funnel performance varying strongly by channel and cohort.  
* ~17% of leads are missing lead_utm_campaign and only ~40% of distinct lead_utm_campaign values are mapped in internal campaign_metadata, creating a large “unattributed/unmapped” bucket.  
* lead_status (“Qualified”, “Nurture”, etc.) does not correlate strongly with conversion, so current SQL‑based views of “good leads” are misleading.

**Next‑sprint deliverables (MVP)**

* fct_marketing_performance: monthly view of spend → sessions → leads → opportunities → customers by source and campaign_group, with CPL and CAC.  
* fct_lead_lifecycle: one row per lead with UTM data, cohort, derived lead_quality, and opportunity/customer outcomes.  
* “Marketing & Sales Performance” dashboard with 3 tabs:  
  * Overview: BANs, funnel over time, and channel breakdown.  
  * Cohorts: cohort heatmap and month‑over‑month (e.g. Sep vs Oct) comparison.  
  * Lead Quality: quality distribution and conversion by source/segment.  
* Basic dbt tests and monitoring on UTM completeness and campaign_metadata coverage to prevent data quality from degrading again.

**Strategic bet (beyond the MVP)**

* Make data quality monitoring and clear ownership of UTMs/campaign_metadata between Marketing and Data the first strategic initiative, so attribution, CAC, and lead‑quality reporting remain trustworthy and can support future work (multi‑touch attribution, advanced lead scoring, and budget reallocation).

# 1. Investigation & Analysis

*What did you discover exploring the data? What business questions need answers? What*  
*problems did you identify? How would you prioritize?*

Details of exact steps taken can be found under Appendix.

**Key quantitative findings**

* ~€260k ad spend over 2 months produced 830 leads, 352 opportunities, and 47 customers; CPL and CAC are high for a B2B SaaS context, with a steep drop‑off from leads to customers.  
* Cohorts by lead_created_at month show October leads converting better than September (higher lead→customer rate), so performance varies meaningfully over time, not just by volume.  
* Conversion by lead_status (New / Contacted / Nurture / Qualified) is very similar, so today’s MQL/SQL logic based on status alone is a weak proxy for “good” leads.

**Data quality issues & unclear logic**

* Around 17% of leads have missing or null UTM fields (especially campaign), and only ~40% of distinct lead_utm_campaign values are mapped in campaign_metadata, creating a persistent “unattributed/unmapped” bucket; in the MVP I surface this explicitly instead of hiding it.  
* Web analytics show inconsistent UTM combinations (e.g., utm_campaign = “Google Brand Campaign” with utm_source = “facebook”), and there is no clear convention on whether these are cross‑channel brand labels or just mis‑tagging.  
* Currency handling and timezones are underspecified: Google Ads and internal cost allocation are explicitly EUR but Facebook has no currency field and everything is implicitly treated as EUR; ad, web, and CRM timestamps may be in different timezones, which can add noise at the day level, though month‑level cohorts remain robust once standardized.

![![][image1]](images/insights.png)

**Source:** Aggregated crm_leads (leadutmsource) + opps/custs JOIN leadid + ad spend UNION. Sep: 5% lead2cust; Oct: 8%.

**Core business questions**

* **Channel & campaign performance:** Which channels (Google, Facebook, non‑paid) and campaign_groups (Brand, Product Launch, Retargeting, Lead Gen) actually drive leads, opportunities, customers, and MRR, and where are we over‑ or under‑invested?  
* **CAC & efficiency:** What are CAC, cost per lead, cost per opportunity, and cost per customer by channel, campaign_group, and cohort (month/quarter)?  
* **Lead quality by source:** Which sources and campaigns consistently produce leads that become opportunities/customers vs those that mostly stall, and where are we over‑optimistic because we only look at volume (impressions, clicks, leads)?  
* **Cohorts & “good leads”:** How do different lead cohorts (e.g. Sep vs Oct) perform over time, and how should we define “good” leads in a way Sales trusts—based on real outcomes (opportunity created, stage, revenue) rather than CRM status labels alone?  
* **Impact of data quality:** How much spend and how many leads are currently unattributed or unmapped, and how would fixing UTMs and campaign_metadata coverage change our view of which channels/campaigns work?

**Problems identified**

* **Data quality & governance:** Incomplete UTM tagging (≈17% missing campaign, ~9% missing source/medium) and partial campaign_metadata coverage (~40% of distinct lead_utm_campaign mapped) guarantee a non‑trivial unattributed/unmapped bucket; questionable UTM combinations in web data further blur channel insights.  
* **Modeling & business logic:** lead_status is a weak proxy for quality; attribution is implicit (no agreed first‑ vs last‑touch, CRM vs web); and CAC definitions are fuzzy (EUR assumed for Facebook, no clear line between media‑only vs fully‑loaded CAC).  
* **Visibility & decision‑making:** There is no single, trusted performance mart linking spend → sessions → leads → opportunities → customers at a consistent grain, so cohort differences (e.g. Oct > Sep) are not explained by channel/campaign/ICP, and Sales and Marketing debate anecdotes instead of shared numbers.  
* **Structural gaps (for later sprints):** Channel taxonomy is not normalized (raw utm_source / lead_utm_source vs a small set of channels like Paid Search, Paid Social, Organic, Direct, Referral); there is no explicit ICP layer; web→lead stitching (sessions/forms to leads) is not modeled; and there is no agreed treatment of non‑paid channels in CAC.

**Prioritization**

* **Short term (next sprint – MVP / quick wins):**  
  * Deliver a marketing performance mart linking Facebook & Google ad spend → Leads → Opportunities → Customers at a monthly × source × campaign_group level using first‑touch UTM attribution and existing campaign_metadata.  
  * Clean up and backfill campaign_metadata so that current CRM UTM campaign strings are mapped to canonical campaign_groups, and surface unattributed/unmapped segments clearly in the mart and dashboard.  
  * Enforce basic UTM completeness for new leads via dbt not_null/accepted_values tests and monitoring, and ship a first dashboard where Marketing and Sales can see CAC, conversion, and cohort performance by channel and campaign_group.  
* **Longer term (following sprints – foundations):**  
  * Run a joint workshop with Marketing and Sales to lock in shared definitions for lead quality, the default attribution model, “paid CAC” vs “fully loaded CAC”, and campaign/UTM standards.  
  * Evolve from simple first‑touch to multi‑touch / journey‑based attribution using web.sessions and web.form_submissions once the basic funnel is trusted.  
  * Formalize data quality monitoring (dbt tests + alerts) around UTMs, campaign mapping, and CRM linkages so that once fixed, these issues stay fixed.

# 2. Data Architecture

*dbt project structure, key models, data flow diagram, naming conventions, materialization*  
*strategy. How will you handle the challenges you found?*

I structure the dbt project into source‑specific staging models, marketing intermediates, and marts that serve as the single source of truth for Marketing and Sales.

**Project structure & key models**

* **Staging (models/staging/)**  
  * Facebook Ads: stg_facebook_ads__basic_campaign, __basic_ad_set, __basic_ad, __ad_history.  
  * Google Ads: stg_google_ads__campaign_stats, __ad_stats.  
  * CRM: stg_crm__leads, stg_crm__opportunities, stg_crm__customers.  
  * Web: stg_web__sessions, stg_web__form_submissions.  
  * Internal: stg_internal__campaign_metadata, stg_internal__cost_allocation.  
* **Marketing intermediates (models/marts/marketing/intermediate/)**  
  * int_marketing__daily_spend_by_campaign: unifies Facebook + Google spend by campaign, date, and platform.  
  * int_marketing__lead_enriched: joins leads to opportunities/customers with lifecycle flags and first_opportunity_* fields.  
  * int_marketing__sessions_with_forms: links sessions and form submissions to model session → form → lead journeys (incl. organic).  
* **Marts & dimensions (models/marts/marketing/)**  
  * fct_marketing_performance: end‑to‑end view of spend → sessions → leads → opportunities → customers and efficiency metrics (CPL, CAC) by month × source × campaign_group.  
  * fct_lead_lifecycle: one row per lead with UTM data, cohort, derived lead_quality, and downstream outcomes.  
  * dim_campaigns: canonical campaign dimension combining internal campaign_metadata with platform campaign identifiers (shared source of truth for campaign_name and campaign_group across CRM, web, and ad platforms).  
  * dim_cost_allocation (or mnl_cost_allocation): cleaned view over finance’s cost_allocation, mapping additional marketing costs (e.g., tools, agencies, brand) into periods and, where possible, campaign_groups to support “full CAC” alongside media‑only CAC.

**Data flow (see diagram)**

![alt text](images/diagram.svg)

All marketing reporting must go through `fct_marketing_performance` and `fct_lead_lifecycle` to keep Marketing and Sales on the same numbers.

**Naming conventions**

* **Layers:** stg_ (staging), int_ (intermediate), fct_ (fact), dim_ (dimension), mnl_ (manual), sum_ (summary).  
* **Namespaces:** domain/source in the name, e.g. stg_crm__leads, stg_web__sessions, stg_internal__campaign_metadata, int_marketing__lead_enriched, fct_marketing_performance, dim_campaigns, dim_cost_allocation.  
* **Grain clarity:** grain added when non‑obvious (e.g. int_marketing__daily_spend_by_campaign is daily × campaign).  
* **Columns:** snake_case with consistent keys (lead_id, account_id, campaign_id, session_id), and re‑used business fields (campaign_group) with identical semantics across models.

**Materialization strategy**

* **Staging (stg_*)** – views: thin, cleaned projections over raw Fivetran tables for cheap, debuggable transforms.  
* **Intermediates (int_marketing__*)** – tables: heavier joins and business logic (spend unification, campaign mapping, lead enrichment, cost allocation), reused by multiple marts.  
* **Marts & dimensions (fct_*, dim_*)** – tables with full refresh at this scale:  
  * fct_marketing_performance: rebuilt daily; can later be incremental on (month, source, campaign_group) if volume grows.  
  * fct_lead_lifecycle: starts as full refresh; can become incremental on lead_created_at with lead_id as unique key.  
  * dim_campaigns, dim_cost_allocation: small dimensions refreshed when upstream metadata or cost input changes.

**Handling key challenges via architecture**

* **Campaign naming & mapping gaps:** stg_internal__campaign_metadata feeds dim_campaigns, which normalizes messy UTM campaign strings (e.g. “…;1004;Cold Traffic;2010”) into canonical campaign_name and campaign_group used consistently in marts and dashboards.  
* **Additional marketing costs & CAC definitions:** dim_cost_allocation standardizes finance’s cost_allocation table and allows us to report both media‑only CAC (ad spend) and full CAC (ad spend + allocated marketing overhead) from the same mart.  
* **Missing/inconsistent UTMs:** staging models preserve nulls; marts surface “Unattributed” / “Unmapped” segments explicitly, while dbt tests measure UTM completeness and mapping coverage over time.  
* **Lead status vs real quality:** int_marketing__lead_enriched and fct_lead_lifecycle derive outcome‑based lead_quality; dashboards rely on it while still exposing raw lead_status.  
* **Attribution & source of truth:** the MVP locks in first‑touch lead‑level UTM attribution, documented in model descriptions; fct_marketing_performance and fct_lead_lifecycle are the only tables used by the Sales & Marketing dashboard for “spend → leads → pipeline → revenue” and cohorts, ensuring everyone sees the same numbers.

# 3. Business Logic

*Define with clear formulas:*  
*● CAC - Calculation, costs included, edge cases*  
*● Lead Quality - Classification criteria, edge cases*  
*● Attribution - Approach, rationale, trade-offs*  
*● Cohort Analysis - Definition, measurement approach*

### CAC - Calculation, costs included, edge cases

**Business definition**  
CAC (Customer Acquisition Cost) tells us how much we spend in marketing to acquire one new paying customer in a given period, for a given segment (e.g., channel, campaign_group, cohort).

**Calculation (conceptual)**  
For a month M, CAC is:

* All marketing costs in that month (ad spend + agreed extra costs)  
* Divided by the number of new customers that started paying in that month, linked back to marketing.

**Formula**  
For month M and segment S (e.g. , channel, campaign_group):

**CAC (M, S) = Total Marketing Cost (M, S) /New Customers (M, S)**  
   
Where:

* Total Marketing Cost (M, S) =  
  * Facebook spent in M,S from facebook_ads.basic_campaign.spend  
  * Google spend in M,S from google_ads.campaign_stats.cost_micros / 1,000,000  
  * Marketing costs in M from internal.cost_allocation (department = Marketing), optionally allocated to segments.  
* New Customers (M,S) =  
  * Distinct account_id in crm.customers with customer_since in month M, joined via crm.opportunities.lead_id to leads whose **attributed channel / campaign_group** is S.

I’d expose:

* `paid_cac` (ad spend only)  
* `full_cac` (ad spend + internal cost_allocation).

**Edge cases**

* If New Customers M,S = 0 → show NULL / “n/a” for CAC (not a huge number).  
* If there is spend but **no mapped leads/customers** (UTM or mapping issues), show this as “Unattributed” segment with its own spend and 0 customers.  
* If customers exist without any paid spend (purely organic), report CAC = 0 for that segment and label it clearly as “Non-paid”.

### Lead Quality

**Business definition**  
Lead quality should reflect **how likely a lead is to turn into real business** (opportunities and customers), not just a subjective CRM status. Sales needs this to prioritize, Marketing to judge sources and campaigns.​

**Calculation (conceptual)**  
Per lead, we look at outcomes:

* Did it create an opportunity?  
* Did it turn into a customer?  
* Was the opportunity meaningful (value/stage)?  
  Then bucket into **High / Medium / Low / Too early**.

**Rules / formula**

Per lead (from int_marketing__lead_enriched):

* Inputs:  
  * `has_opportunity` (TRUE/FALSE)  
  * `is_customer` (TRUE/FALSE)  
  * `first_opportunity_amount`  
  * `first_opportunity_stage`  
  * `lead_created_at` (to compute age).  
* Logic:

```sql
IF is_customer   
   OR (has_opportunity   
       AND first_opportunity_amount > median_opp_amount  
       AND first_opportunity_stage IN ('Proposal', 'Negotiation', 'Closed Won')  
)  
   THEN lead_quality = 'High'  
ELSE IF has_opportunity   
   THEN lead_quality = 'Medium'  
ELSE IF lead_age_days <= 14  
   THEN lead_quality = 'Too early'  
ELSE  
   lead_quality = 'Low'  
END
```

**Edge cases**

* Very recent leads (lead_age_days <= 14) are tagged as **“Too early”** so we don’t punish new campaigns.​  
* Leads with broken linkage (no opportunity_id despite evidence elsewhere) will fall into “Low” but we can additionally flag them as “unlinked” for data cleanup.  
* We keep lead_status (New/Contacted/Nurture/Qualified/Not Interested) for context, but we explicitly **don’t** use it as the primary definition because its conversion patterns are noisy.

### Attribution

**Business definition**  
Attribution answers: **which channel/campaign should get credit** for the pipeline and revenue we see, so we can shift budget intelligently

**Calculation (conceptual)**  
For this MVP, we:

* Assign each lead to **one** campaign/source/medium based on how it first entered the CRM (first-touch).  
* Aggregate spend and outcomes by that attribution.

**Rules / formula**

Per lead:

* attributed_source:  
  * lead_utm_source, or  
  * if null, inferred from campaign_metadata.platform (facebook/google/linkedin), else 'unknown'.  
* attributed_medium:  
  * lead_utm_medium or 'unknown'.​  
* attributed_campaign & attributed_campaign_group:  
  * From int_marketing__campaigns_normalized, which maps raw lead_utm_campaign via internal.campaign_metadata.

Then for each (month, attributed_source, attributed_campaign_group):

* leads = count of leads.  
* opps = count of leads that became opps.  
* customers = count of leads that became customers.  
* spend = ad spend from FB/Google mapped into that (month, source, campaign_group).

**Rationale**

* lead_utm_* is the cleanest, most complete attribution signal we have today; session-level chains are not modeled yet.  
* First-touch is enough to answer “what should we keep funding to acquire new leads/customers?” within one sprint.

**Trade-offs**

* We ignore multi-touch / last-touch influence (e.g. Retargeting campaigns that help close).  
* Leads with missing UTMs are bucketed as source = 'unknown' / campaign_group = 'Unmapped', which we can track and try to shrink as data quality improves.  
* Future extension: build session + form → lead journeys and add a **second model** (e.g. position-based) rather than silently changing the first-touch logic.

### Cohort Analysis

**Business definition**  
Cohort analysis asks: **do leads acquired in a given time / campaign context behave differently over their lifetime?** Think “Sep cohort vs Oct cohort” and “Brand vs Retargeting cohorts.”

**Calculation (conceptual)**  
We group leads by a **cohort key** (e.g. acquisition month + campaign_group) and then track how many of them become opportunities/customers and how much revenue they generate over time.

**Rules / formula**

Primary cohort key:

* cohort_month = date_trunc('month', lead_created_at).

Additional dimensions:

* cohort_campaign_group = attributed_campaign_group (Brand Awareness, Product Launch, Retargeting, Lead Gen, Other).  
* cohort_source = attributed_source.

Per cohort (cohort_month, cohort_campaign_group, cohort_source):

* leads = count of leads.  
* opps = count with has_opportunity = 1.  
* customers = count with is_customer = 1.  
* lead_to_opp_rate = opps / leads.  
* lead_to_customer_rate = customers / leads.  
* avg_opp_value = avg opportunity amount.​  
* Optional: 30/60/90-day conversion if we define fixed time windows.

**Edge cases**

* Very small cohorts (e.g., only a few leads) should be flagged or hidden by default to avoid over-interpreting noise (e.g. the tiny Nov cohort).  
* Late conversions (customers created long after the cohort month) should either:  
  * be included with a fixed observation window (e.g., 90 days after lead_created), or  
  * be clearly documented as “lifetime to date” to avoid confusion in early cohorts.

# 4. dbt Models

*3-4 examples with SQL, config, documentation, tests:*  
*● 1 staging model*  
*● 1 intermediate model*  
*● 1 mart model*

### 1 staging model - `staging__stg_crm_leads`

**Purpose**  
Clean CRM leads, standardize UTM fields, and cast timestamps for attribution, cohorts, and lead quality.

```sql
{{ config(  
  materialized = 'view',  
  schema = 'staging',  
  alias = 'stg_crm_leads',  
  tags = ['staging', 'crm']  
) }}

with source as (  
  select * from {{ source('crm', 'leads') }}  
)

select  
  lead_id,  
  email,  
  lead_created_at::timestamp          as lead_created_at,  
  nullif(lead_utm_campaign, '')       as lead_utm_campaign_raw,  
  lower(nullif(lead_utm_source, ''))  as lead_utm_source,  
  lower(nullif(lead_utm_medium, ''))  as lead_utm_medium,  
  lower(nullif(lead_utm_content, '')) as lead_utm_content,  
  lower(nullif(lead_utm_term, ''))    as lead_utm_term,  
  company_name,  
  industry,  
  country,  
  lead_status  
from source;

```

**Key tests (schema.yml excerpt)**

```yml
version: 2

models:  
  - name: staging__stg_crm_leads  
    description: "Cleaned CRM leads with standardized UTM fields and timestamps."  
    meta:  
      owner: data-team  
      business_purpose: "Base model for attribution, cohorts, and lead quality."  
    columns:  
      - name: lead_id  
        description: "Unique identifier for a lead in the CRM."  
        tests: [not_null, unique]  
      - name: lead_created_at  
        description: "Timestamp when the lead was created."  
        tests: [not_null]  
      - name: lead_utm_campaign_raw  
        description: "Raw UTM campaign string as captured in the CRM."  
      - name: lead_utm_source  
        description: "UTM source (google, facebook, linkedin, etc.)."  
      - name: lead_status  
        description: "CRM lead status (New, Contacted, Nurture, Qualified, Not Interested)."

```

### Intermediate model – `intermediate__int_marketing_lead_enriched`

**Purpose**  
Enrich each lead with its first opportunity and downstream customer, and derive lifecycle flags (has_opportunity, is_customer). This is the backbone for lead quality, cohorts, and the marketing mart.

```sql
{{ config(  
  materialized = 'table',  
  schema = intermediate,  
  alias = 'int_marketing_lead_enriched',  
  tags = ['marketing', 'intermediate']  
) }}

with leads as (  
  select * from {{ ref('staging__stg_crm_leads') }}  
),

opportunities as (  
  select  
    lead_id,  
    account_id,  
    opportunity_id,  
    opportunity_created_at::timestamp as opportunity_created_at,  
    stage_name,  
    amount  
  from {{ ref('staging__stg_crm_opportunities') }}  
),

customers as (  
  select  
    account_id,  
    customer_since::date as customer_since,  
    mrr,  
    churn_date::date      as churn_date  
  from {{ ref('staging__stg_crm_customers') }}  
),

lead_first_opportunity as (  
  select  
    lead_id,  
    min_by(opportunity_id, opportunity_created_at) as first_opportunity_id,  
    min(opportunity_created_at)                    as first_opportunity_created_at  
  from opportunities  
  group by lead_id  
),

opportunity_with_customer as (  
  select  
    opportunities.opportunity_id,  
    opportunities.lead_id,  
    opportunities.account_id,  
    opportunities.stage_name,  
    opportunities.amount,  
    customers.customer_since,  
    customers.mrr,  
    customers.churn_date  
  from opportunities  
  left join customers  
    on opportunities.account_id = customers.account_id  
)

select  
  leads.*,  
  lead_first_opportunity.first_opportunity_id,  
  opportunity_with_customer.stage_name  as first_opportunity_stage,  
  opportunity_with_customer.amount      as first_opportunity_amount,  
  opportunity_with_customer.customer_since,  
  opportunity_with_customer.mrr,  
  opportunity_with_customer.churn_date,  
  case when lead_first_opportunity.first_opportunity_id is not null then 1 else 0 end as has_opportunity,  
  case when opportunity_with_customer.customer_since      is not null then 1 else 0 end as is_customer  
from leads  
left join lead_first_opportunity  
  on leads.lead_id = lead_first_opportunity.lead_id  
left join opportunity_with_customer  
  on lead_first_opportunity.first_opportunity_id = opportunity_with_customer.opportunity_id;

```

**Key tests (schema.yml excerpt)**

```yml
version: 2

models:  
  - name: intermediate__int_marketing_lead_enriched  
    description: "Leads enriched with first opportunity and customer info plus lifecycle flags."  
    meta:  
      owner: data-team  
      business_purpose: "Base for lead quality, cohorts, and marketing performance."  
    columns:  
      - name: lead_id  
        tests: [not_null, unique]  
      - name: first_opportunity_id  
        description: "ID of the first opportunity created from this lead (if any)."  
      - name: has_opportunity  
        description: "1 if the lead created at least one opportunity."  
        tests:  
          - accepted_values:  
              values: [0, 1]  
      - name: is_customer  
        description: "1 if the lead eventually became a customer."  
        tests:  
          - accepted_values:  
              values: [0, 1]  
      - name: account_id  
        description: "Account linked to the first opportunity (if present)."
```

### Mart model - marts__fct_marketing_performance

**Purpose**  
Combine media spend, web sessions, and enriched leads into a single monthly × source × campaign_group mart with funnel and efficiency metrics (sessions, leads, opps, customers, pipeline, CPL, CAC, conversion rates).

Note: If this model becomes too heavy in the future, the CTEs can be moved upstream and become separate intermediate models themselves.

```sql
{{ config(  
  materialized = 'table',  
  schema = 'marts,  
  alias = 'fct_marketing_performance',  
  tags = ['marketing', 'mart']  
) }}

with facebook_spend as (  
  select  
    date_trunc('month', date) as month,  
    'facebook'::text          as source,  
    campaign_id,  
    spend::numeric            as spend_eur  
  from {{ ref('staging__stg_facebook_ads_basic_campaign') }}  
),

google_spend as (  
  select  
    date_trunc('month', date)          as month,  
    'google'::text                     as source,  
    campaign_id,  
    (cost_micros::numeric / 1_000_000) as spend_eur  
  from {{ ref('staging__stg_google_ads_campaign_stats') }}  
),

union_spend as (  
  select month, source, campaign_id, spend_eur from facebook_spend  
  union all  
  select month, source, campaign_id, spend_eur from google_spend  
),

campaign_metadata as (  
  select  
    utm_campaign_name as utm_campaign_raw,  
    platform,  
    actual_campaign_name,  
    campaign_group  
  from {{ ref('staging__stg_internal_campaign_metadata') }}  
),

marketing_leads as (  
  select  
    date_trunc('month', lead_created_at)          as month,  
    coalesce(lead_utm_source, 'unknown')         as source,  
    coalesce(cm.campaign_group, 'Unmapped')      as campaign_group,  
    has_opportunity,  
    is_customer,  
    coalesce(first_opportunity_amount, 0)        as opportunity_amount  
  from {{ ref('intermediate__int_marketing__lead_enriched') }} l  
  left join campaign_metadata cm  
    on l.lead_utm_campaign_raw = cm.utm_campaign_raw  
),

aggregated_leads as (  
  select  
    month,  
    source,  
    campaign_group,  
    count(*)                     as leads,  
    sum(has_opportunity)         as opportunities,  
    sum(is_customer)             as customers,  
    sum(opportunity_amount)      as pipeline_value  
  from marketing_leads  
  group by month, source, campaign_group  
),

aggregated_spend as (  
  select  
    month,  
    source,  
    'All'::text as campaign_group,  
    sum(spend_eur) as ad_spend_eur  
  from union_spend  
  group by month, source, campaign_group  
),

web_sessions as (  
  select  
    date_trunc('month', session_timestamp) as month,  
    coalesce(utm_source, 'unknown')        as source,  
    utm_campaign                           as utm_campaign_raw,  
    count(*)                               as sessions  
  from {{ ref('staging__stg_web_sessions') }}  
  group by month, source, utm_campaign_raw  
),

web_sessions_with_group as (  
  select  
    ws.month,  
    ws.source,  
    coalesce(cm.campaign_group, 'Unmapped') as campaign_group,  
    ws.sessions  
  from web_sessions ws  
  left join campaign_metadata cm  
    on ws.utm_campaign_raw = cm.utm_campaign_raw  
),

aggregated_web_traffic as (  
  select  
    month,  
    source,  
    campaign_group,  
    sum(sessions) as sessions  
  from web_sessions_with_group  
  group by month, source, campaign_group  
)

select  
  coalesce(al.month, aspend.month, awt.month)                          as month,  
  coalesce(al.source, aspend.source, awt.source)                        as source,  
  coalesce(al.campaign_group, aspend.campaign_group, awt.campaign_group) as campaign_group,  
  coalesce(aspend.ad_spend_eur, 0)                                     as ad_spend_eur,  
  coalesce(awt.sessions, 0)                                            as sessions,  
  coalesce(al.leads, 0)                                                as leads,  
  coalesce(al.opportunities, 0)                                        as opportunities,  
  coalesce(al.customers, 0)                                            as customers,  
  coalesce(al.pipeline_value, 0)                                       as pipeline_value,  
  case when sessions   > 0 then leads::numeric       / sessions   end  as visit_to_lead_rate,  
  case when leads      > 0 then ad_spend_eur         / leads      end  as cost_per_lead,  
  case when customers  > 0 then ad_spend_eur         / customers  end  as paid_cac,  
  case when leads      > 0 then opportunities::numeric / leads    end  as lead_to_opportunity_rate,  
  case when leads      > 0 then customers::numeric     / leads    end  as lead_to_customer_rate  
from aggregated_leads al  
full outer join aggregated_spend       aspend on al.month = aspend.month  
                                       and al.source = aspend.source  
                                       and al.campaign_group = aspend.campaign_group  
full outer join aggregated_web_traffic awt    on coalesce(al.month,   aspend.month)   = awt.month  
                                       and coalesce(al.source, aspend.source)        = awt.source  
                                       and coalesce(al.campaign_group, aspend.campaign_group) = awt.campaign_group;

```

**Key tests (schema.yml excerpt)**

```yml
version: 2

models:  
  - name: mart__fct_marketing_performance  
    description: >  
      Monthly marketing performance by source and campaign_group with spend,  
      sessions, funnel metrics, and efficiency (CPL, CAC, conversion rates).  
    meta:  
      owner: data-team  
      business_purpose: "Single source of truth for Marketing & Sales to discuss channel and campaign performance."  
    columns:  
      - name: month  
        description: "Reporting / cohort month (first day of the month)."  
        tests: [not_null]  
      - name: source  
        description: "Attributed traffic/source channel (facebook, google, linkedin, direct, organic, unknown)."  
      - name: campaign_group  
        description: "Canonical campaign grouping (Brand Awareness, Product Launch, Retargeting, Lead Gen, Other, Unmapped)."  
      - name: ad_spend_eur  
        description: "Paid media spend in EUR from Facebook and Google for this month/source."  
      - name: sessions  
        description: "Number of web sessions for this month/source/campaign_group (paid + organic)."  
      - name: leads  
        description: "Number of leads created in this month/source/campaign_group."  
        tests: [not_null]  
      - name: customers  
        description: "Number of leads in this segment that became customers."  
        tests: [not_null]  
      - name: cost_per_lead  
        description: "Ad spend per lead (media-only CPL)."  
      - name: paid_cac  
        description: "Ad spend per new customer (media-only CAC)."
```


# 5. Dashboard Design

*Layout, visualizations, key metrics, filters, access controls*

I’d ship a single “Marketing & Sales Performance” dashboard with three tabs: Overview, Cohorts, and Lead Quality, all powered by the two marts (fct_marketing_performance, fct_lead_lifecycle) and a thin reporting layer.

## **Tab 1 – Overview**

**Purpose**  
Give Marketing, Sales, and leadership one place to answer “how are we doing overall?” for a selected period.

**Layout**

* **Top row – KPI tiles (with Δ vs previous period)**  
  * Total ad spend (EUR).  
  * Total sessions.  
  * Total leads, opportunities, customers.  
  * Overall paid CAC (media only).  
  * Overall lead→customer rate.  
* **Main chart – funnel over time (combo)**  
  * X‑axis: month (or week).  
  * Lines: impressions, sessions, leads, customers.  
  * Bars: ad_spend_eur.  
  * Shows how top‑of‑funnel and spend relate to conversions over time.  
* **Channel breakdown (table + bar chart)**  
  * Table, one row per source (facebook, google, organic, direct, unknown, etc.; optionally campaign_group = “All”):  
    * sessions, leads, opportunities, customers, pipeline_value, visit_to_lead_rate, lead_to_customer_rate, ad_spend_eur, cost_per_lead, paid_cac.  
  * Side bar chart: X‑axis = source; bars = customers; line = paid_cac.

**Filters (global)**

* Date range (default last 3 months, month granularity).  
* Source.  
* Campaign_group.  
* Country, industry.  
  ---

## **Tab 2 – Cohort View**

**Purpose**  
Answer “Are newer cohorts better?” and “Which campaign_groups/sources actually create strong cohorts?”

**Layout**

* **Cohort heatmap** (from fct_lead_lifecycle aggregated by (cohort_month, campaign_group)):  
  * X‑axis: cohort_month (Sep, Oct, …).  
  * Y‑axis: campaign_group (Brand Awareness, Product Launch, Retargeting, Lead Gen, Other, Unmapped).  
  * Cell: primary = lead_to_customer_rate; toggle = customers per 100 leads.  
* **Cohort comparison small multiples**  
  * One tile per cohort_month (e.g., Sep vs Oct).  
  * Within each tile: bar chart by campaign_group showing leads, customers, and lead_to_customer_rate.  
  * Makes it obvious, for example, that Oct cohorts outperform Sep and which campaign_groups drive the difference.  
* **Optional second heatmap**  
  * X‑axis: cohort_month, Y‑axis: source, cell = lead_to_customer_rate.

**Filters**

* Cohort_month range.  
* Campaign_group.  
* Source.  
* Country, industry.  
  ---

## **Tab 3 – Lead Quality View**

**Purpose**  
Help Sales and Marketing understand where High/Medium/Low quality leads come from and how they convert, so they can prioritize work and budget.

**Layout**

* **Lead quality distribution** (from fct_lead_lifecycle):  
  * Stacked bar chart:  
    * X‑axis: source.  
    * Stack: lead_quality (High / Medium / Low / Too early).  
    * Y‑axis: number of leads.  
  * Shows which channels skew towards high‑quality vs low‑quality leads.  
* **Quality vs conversion table**  
  * Grouped by (source, lead_quality):  
    * leads, opportunities, customers, lead_to_customer_rate, optional average opportunity amount.  
  * Answers: “For each channel, what share of leads are actually High quality, and how do they convert?”  
* **Optional ICP / segment drill‑down**  
  * Filters/columns for country and industry to slice within High‑quality leads (e.g. “High‑quality DACH Manufacturing leads via Retargeting”).


## **Access & ownership**

* Marketing & Sales: read‑only access to all 3 tabs.  
* Data team: full edit rights and ownership of the marts, definitions, and reporting layer.

# 6. Stakeholder Communication

*15-minute meeting outline: findings, questions needed, decisions required, timeline*

**0–3 min – Context & goal**

* Remind them of the ask: “€50k+/month on ads, no clarity on what works, Sales says leads are bad, no cohort view.”  
* Say what was done: pulled FB/Google, web, CRM, and internal cost/campaign data; built a draft spend → web → lead → opp → customer model.  
* **Goal of this meeting**: agree on logic + decisions so we can ship an MVP dashboard next sprint.

**3–7 min – Key findings**

* Funnel snapshot: ~€260k spend → 830 leads → 352 opps → 47 customers; CAC and CPL are high but not hopeless.  
* Data issues:  
  *  ~17% leads missing UTM campaign, partial campaign_metadata coverage (~40% of CRM campaigns mapped), odd UTM combos in web data.  
* Process issue:   
  * lead_status doesn’t track true quality;   
  * “Nurture” converts nearly as well as “Qualified”.  
* Signal:  
  *  Oct cohorts perform better than Sep;   
  * Some sources/campaign_groups clearly outperform, but this isn’t visible today.

**7–11 min – Proposed solution (MVP)**

* Data models:  
  * fct_marketing_performance: monthly performance by source × campaign_group (sessions, leads, opps, customers, pipeline, CPL, CAC).  
  * fct_lead_lifecycle: per-lead lifecycle with UTM, cohort_month, lead_quality, outcomes.  
* Business logic:  
  * CAC: show paid CAC and full CAC (with internal cost allocation).  
  * Lead quality: High / Medium / Low / Too early based on opp/customer outcomes, not CRM status.  
  * Attribution: first-touch UTM at lead level as default; multi-touch as a later extension.  
* Dashboard:  
  * Tab 1: Overview (BANs + combo chart + channel breakdown).  
  * Tab 2: Cohorts (cohort heatmap, Sep vs Oct).  
  * Tab 3: Lead quality (quality by source/ICP).

**11–13 min – Questions/decisions needed**

* Attribution: OK to use **first-touch** as the official MVP model (and add multi-touch later as a separate view)?  
* CAC scope: should “default” CAC be media-only, full, or do we always show both?  
* Lead quality: do the High/Medium/Low rules (based on opp/customer) match how Sales thinks about “good leads”, or any tweaks?  
* Ownership: who in Marketing owns UTMs and campaign_metadata so that mapping gaps get fixed at source?​

**13–15 min – Timeline & next steps**

* Next sprint (2 weeks):  
  * Implement dbt models + tests and ship the 3-tab dashboard.  
  * Start tracking UTM completeness and campaign mapping coverage.  
* Following sprint:  
  * Iterate on definitions (lead quality thresholds, CAC view), add Finance tab if wanted, and explore multi-touch attribution using web sessions + forms.

# 7. Strategic Recommendation - Data Quality Monitoring

Why this first?

* All the key questions (which campaigns work, which channels bring good leads, which cohorts are better) depend on **UTM quality, campaign mapping, and CRM linkages** being consistently correct.  
* Right now:  
  * ~17% of leads are missing lead_utm_campaign.  
  * Only ~40% of CRM campaigns are mapped in campaign_metadata.  
  * Web UTMs are inconsistent, and lead_status doesn’t reflect true quality.  
* If we don’t monitor and enforce this, any attribution/CAC model will degrade again in a few weeks.

### What I’d implement

**1. dbt tests on critical fields**

* On stg_crm__leads and stg_web__form_submissions:  
  * Not-null tests on lead_utm_campaign, lead_utm_source, utm_campaign, utm_source (with some allowed % of nulls initially).  
* On stg_internal__campaign_metadata:  
  * Relationship tests to ensure all “used” UTM campaign values in CRM and web are either mapped or explicitly flagged as unmapped.  
* On int_marketing__lead_enriched / fct_marketing_performance:  
  * Sanity checks on rates (e.g., lead_to_customer_rate between 0 and 1).

**2. Simple monitoring & alerting**

* Daily dbt run that:  
  * Calculates **UTM completeness %** (e.g., share of leads with non-null UTM campaign/source).  
  * Calculates **campaign mapping coverage %** (share of lead_utm_campaign values mapped in campaign_metadata).  
* Push a short summary to Slack/Teams:  
  * “Yesterday: 92% leads with UTM campaign, 80% campaign strings mapped. Target: 98% / 100%.”​

**3. Clear ownership & process**

* Nominate:  
  * A **Marketing owner** for UTMs and campaign_metadata (creates entries before new campaigns go live, fixes unmapped ones).​​  
  * The **Data team** as owner of tests and monitoring (they surface issues, not fix tags in ad tools/web).  
* Lightweight rules:  
  * New campaign checklist: UTM structure, entry in campaign_metadata, agreed campaign_group, platform.  
  * Quarterly review: clean up “Unmapped/Unknown” buckets and update mapping.

### Impact

* Marketing and Sales get a performance dashboard they can **trust over time**, not just for this case study.  
* A feedback loop is created: every time someone breaks UTMs or adds an unmapped campaign, it shows up in the metrics and gets fixed quickly.  
* This makes later investments (multi-touch attribution, more complex lead scoring, better tools) actually worth it.

# Appendix

## Links

* Exploration Conversation with AI (Perplexity): [https://www.perplexity.ai/search/so-here-i-ve-got-the-take-home-Z6dVz64uSnCAMxHtPwS8pg#18](https://www.perplexity.ai/search/so-here-i-ve-got-the-take-home-Z6dVz64uSnCAMxHtPwS8pg#18)  
* Revision Conversation with AI (Perplexity): [https://www.perplexity.ai/search/hi-i-am-finalizing-the-take-ho-l6WSIc2_SP6tDehUS2HZuw#0](https://www.perplexity.ai/search/hi-i-am-finalizing-the-take-ho-l6WSIc2_SP6tDehUS2HZuw#0)  
* Final Review Conversation with AI (Perplexity): [https://www.perplexity.ai/search/hi-i-am-finalizing-the-take-ho-GJDCkcDCQWGyTDvaFYlzug#0](https://www.perplexity.ai/search/hi-i-am-finalizing-the-take-ho-GJDCkcDCQWGyTDvaFYlzug#0)

# Details Steps done for Investigation & Analysis

# Interpreted Context

First, I looked at the business scenario to establish a basic understanding of:

1. Who are the stakeholders? (Answer: Marketing team and Sales team)  
2. What are the “asks”:  
   1. By Marketing:  
      1. No visibility of what spending on the campaign is paying off  
   2. By Sales:  
      1. Generated Leads are going nowhere  
      2. Need to know which lead is actually value adding  
      3. No visibility on Cohort performance (e.g., can't answer questions like “are Q1 leads converting better than Q2?”)  
   3. In other words, it appears that there is a mismatch problem of Ads on Facebook & Google not attracting the right kind of customers (the kind that would be valuable leads and convert into actual business), judging by the stakeholder feedbacks  
3. Expected ETA: need something at least basic up & running before next Sprint  
   

# Data Discovery

Then, I establish a high-level overview of all existing data to have an idea of what applications are generating the data (i.e., Facebook Ads, Google Ads, Web Tracking, and internal applications):  
![alt text](images/data_discovery.png)

Then, I read the content of DATA_DICTIONARY.MD to obtain a better understanding of all given data. Basically, here are the “roles” per CSV files:

* Facebook Ads  
  * account_history: a Dimension table of all company Facebook Ads account  
  * Basic_campaign: a Summary table that aggregate Ad performance in terms of # Impressions, # Inline link Clicks , and Cost on the level of Campaign, Account, and daily level  
  * Basic_ad: a Summary table that aggregate Ad performance in terms of # Impressions, # Inline link Clicks , Spending on the level of Ad, Facebook Account ID, and daily level  
  * Basic_ad_set: a Summary table that aggregate Ad performance in terms of Spending on the level of Ad Set, Campaign, and daily level  
  * Ad_history: a Dimension table of Facebook Ads, along with their related Ad Set IDs, Campaign ID, and related Facebook Ad account ID  
* Google Ads  
  * Campaign_stats: a Summary table that aggregate Ad performance in terms of # Impressions, # Clicks, Cost micros on the level of Campaign, and daily level  
  * Ad_stats: a Summary table that aggregate Ad performance in terms of # Impressions, # Clicks, Cost micros on the level of Campaign, and daily level  
* CRM data  
  * Leads: A Fact table of all CRM leads. Which wraps potential JOIN keys in concatenate STRING values like Retargeting Campaign;1003;Retargeting;2007. Usable for analytical purposes but pretty bad key in strict data engineering sense  
  * Opportunities: A Fact table of all CRM Opportunities, which is a step happening after Leads. Also has good Forigen Key to use to JOIN Leads.  
  * customers: A Dimension table of Customers, along with  their MRR and churn date (only populated if churned)  
* Web analytics data  
  * Sessions: A Fact table of all web tracking data in terms of Sessions, likely coming from Google Analytics. It also contains the session level of Page Views & Duration  
  * Form_submissions: A Fact table of Form Submission in Web.  
* Internal Data  
  * campaign_metadata: A Dimension table of all Marketing Campaigns, should be a good source of truth in terms of all Campaigns across different platforms  
  * Cost_allocation: A Fact table of all additional Marketing costs reported by the Finance team.
