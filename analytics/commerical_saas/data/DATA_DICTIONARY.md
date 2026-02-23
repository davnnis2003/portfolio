# Data Dictionary

---

## Facebook Ads Data (via Fivetran)

### facebook_ads.account_history
Account-level metadata.

| Column | Type |
|--------|------|
| account_id | INT |
| account_name | STRING |
| account_country | STRING |
| _fivetran_synced | TIMESTAMP |

**Rows:** 3

---

### facebook_ads.basic_campaign
Campaign-level daily performance data.

| Column | Type |
|--------|------|
| campaign_id | INT |
| campaign_name | STRING |
| account_id | INT |
| date | DATE |
| spend | DECIMAL |
| impressions | INT |
| inline_link_clicks | INT |

**Rows:** ~595

---

### facebook_ads.basic_ad_set
Ad set (ad group) level daily performance data.

| Column | Type |
|--------|------|
| ad_set_id | INT |
| ad_set_name | STRING |
| campaign_id | INT |
| date | DATE |
| spend | DECIMAL |
| impressions | INT |
| inline_link_clicks | INT |

**Rows:** ~1,624

---

### facebook_ads.ad_history
Ad-level metadata and relationships.

| Column | Type |
|--------|------|
| ad_id | INT |
| ad_name | STRING |
| ad_set_id | INT |
| campaign_id | INT |
| account_id | INT |
| _fivetran_synced | TIMESTAMP |

**Rows:** ~106

---

### facebook_ads.basic_ad
Ad-level daily performance data.

| Column | Type |
|--------|------|
| ad_id | INT |
| date | DATE |
| spend | DECIMAL |
| impressions | INT |
| inline_link_clicks | INT |
| account_id | INT |

**Rows:** ~4,784

---

## Google Ads Data (via Fivetran)

### google_ads.campaign_stats
Campaign-level daily performance data.

| Column | Type |
|--------|------|
| campaign_id | INT |
| campaign_name | STRING |
| date | DATE |
| cost_micros | INT |
| clicks | INT |
| impressions | INT |

**Rows:** ~214
**Note:** cost_micros should be divided by 1,000,000 for EUR

---

### google_ads.ad_stats
Ad-level daily performance data.

| Column | Type |
|--------|------|
| ad_id | INT |
| ad_name | STRING |
| campaign_id | INT |
| campaign_name | STRING |
| date | DATE |
| cost_micros | INT |
| clicks | INT |
| impressions | INT |

**Rows:** ~799
**Note:** cost_micros should be divided by 1,000,000 for EUR

---

## CRM Data

### crm.leads
Lead records with UTM parameters.

| Column | Type |
|--------|------|
| lead_id | STRING |
| email | STRING |
| lead_created_at | TIMESTAMP |
| lead_utm_campaign | STRING |
| lead_utm_source | STRING |
| lead_utm_medium | STRING |
| lead_utm_content | STRING |
| lead_utm_term | STRING |
| company_name | STRING |
| industry | STRING |
| country | STRING |
| lead_status | STRING |

**Rows:** ~830

---

### crm.opportunities
Sales pipeline data.

| Column | Type |
|--------|------|
| opportunity_id | STRING |
| lead_id | STRING |
| account_id | STRING |
| opportunity_created_at | TIMESTAMP |
| stage_name | STRING |
| amount | DECIMAL |
| close_date | DATE |

**Rows:** ~352

---

### crm.customers
Closed-won customer data.

| Column | Type |
|--------|------|
| account_id | STRING |
| customer_since | DATE |
| mrr | DECIMAL |
| churn_date | DATE |

**Rows:** ~47

---

## Web Analytics Data

### web.sessions
Website visitor session data with UTM parameters.

| Column | Type |
|--------|------|
| session_id | STRING |
| session_timestamp | TIMESTAMP |
| utm_campaign | STRING |
| utm_source | STRING |
| utm_medium | STRING |
| page_views | INT |
| duration_seconds | INT |

**Rows:** ~2,000

---

### web.form_submissions
Lead form submissions and content downloads.

| Column | Type |
|--------|------|
| form_id | STRING |
| session_id | STRING |
| submitted_at | TIMESTAMP |
| form_type | STRING |
| utm_campaign | STRING |
| utm_source | STRING |
| utm_medium | STRING |

**Rows:** ~300

---

## Internal Data

### internal.campaign_metadata
Manual campaign reference data.

| Column | Type |
|--------|------|
| utm_campaign_name | STRING |
| platform | STRING |
| actual_campaign_name | STRING |
| campaign_group | STRING |

**Rows:** 10

---

### internal.cost_allocation
Additional marketing costs from Finance.

| Column | Type |
|--------|------|
| month | STRING |
| cost_type | STRING |
| amount | DECIMAL |
| currency | STRING |
| department | STRING |

**Rows:** 10
