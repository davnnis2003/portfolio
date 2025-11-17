# Modern Data Stack Architecture: Design Patterns & Best Practices

*Lessons from implementing dbt + Snowflake + Airflow across multiple organizations*

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Sources                             │
│  (Applications, SaaS Tools, Databases, APIs, Event Streams)     │
└───────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Ingestion Layer                              │
│          (Fivetran, Airbyte, Custom Python Scripts)            │
└───────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Data Warehouse (Snowflake)                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  RAW Layer   │  │ STAGING Layer│  │  MARTS Layer │        │
│  │              │→ │              │→ │              │        │
│  │ (Raw data)   │  │ (Cleaned)    │  │ (Business)   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                  │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                Transformation Layer (dbt)                        │
│     (Data Modeling, Testing, Documentation, Lineage)            │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│               Orchestration (Airflow)                            │
│          (Scheduling, Monitoring, Dependencies)                  │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Data Quality (Elementary)                        │
│            (Testing, Alerting, Monitoring)                       │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                 BI & Analytics Layer                             │
│          (Tableau, Looker, Python Notebooks)                    │
└─────────────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    End Users                                     │
│      (Business Stakeholders, Analysts, Data Scientists)         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Design Patterns

### 1. RAW Layer

**Purpose:** Preserve source data exactly as received

**Design Principles:**
- Immutable (never modify raw data)
- Full historical load where possible
- Minimal transformation (type casting only)
- Source system naming preserved

**Naming Convention:**
```
raw_{source_system}_{object_name}

Examples:
- raw_salesforce_accounts
- raw_stripe_invoices
- raw_ga4_events
```

### 2. STAGING Layer

**Purpose:** Clean and standardize data from raw sources

**Design Principles:**
- One staging model per raw source
- Type casting and renaming
- Deduplication if needed
- Basic data quality checks
- No business logic yet

**Naming Convention:**
```
stg_{source_system}__{object_name}

Examples:
- stg_salesforce__accounts
- stg_stripe__invoices
- stg_ga4__events
```

### 3. MARTS Layer

**Purpose:** Business-ready data models for analytics

**Design Principles:**
- Organized by business domain
- Denormalized for query performance
- Business-friendly naming
- Comprehensive documentation
- SLAs defined

**Naming Convention:**
```
{domain}__{entity}

Examples:
- finance__revenue_by_month
- marketing__campaign_performance
- operations__order_fulfillment_metrics
```

---

## Data Quality Framework

### Testing Strategy

**Test Pyramid:**
```
        ┌─────────────────┐
        │  Business Logic │  (10% of tests)
        │     Tests       │  - Metric calculations correct
        └─────────────────┘  - Business rules enforced
              ▲
              │
      ┌───────────────────┐
      │   Integrity Tests │  (30% of tests)
      │                   │  - Referential integrity
      └───────────────────┘  - Freshness checks
              ▲              - Distribution checks
              │
  ┌───────────────────────────┐
  │   Foundational Tests      │  (60% of tests)
  │                           │  - unique, not_null
  └───────────────────────────┘  - accepted_values
                                  - relationships
```

### Elementary Integration

**Anomaly Detection:**
```yaml
# models/marts/finance/finance__revenue.yml
models:
  - name: finance__revenue
    tests:
      - elementary.volume_anomalies:
          timestamp_column: 'revenue_month'
      
      - elementary.all_columns_anomalies:
          timestamp_column: 'revenue_month'
```

---

## Performance Optimization

### Materialization Strategy

**Guidelines:**
- **Small, frequently changing:** View
- **Medium, updated daily:** Table
- **Large, append-only:** Incremental

### Snowflake-Specific Optimizations

**Clustering:**
```sql
-- High cardinality dimensions
ALTER TABLE finance__revenue CLUSTER BY (revenue_month, product_category);

-- Time-series data
ALTER TABLE fct_events CLUSTER BY (event_date);
```

---

## Documentation Best Practices

### Model Documentation

```yaml
models:
  - name: finance__revenue
    description: >
      **Revenue metrics aggregated by month, product category, and sales channel.**
      
      **Use Cases:**
      - Monthly revenue reporting to executives
      - Product performance analysis
      - Channel attribution modeling
      
      **SLA:** Updated daily by 6 AM UTC
      **Owner:** Finance Analytics Team
```

---

## Governance & Access Control

### Snowflake RBAC

```sql
-- Role hierarchy
CREATE ROLE data_analyst;
CREATE ROLE data_engineer;
CREATE ROLE data_admin;

-- Grant hierarchy
GRANT ROLE data_analyst TO ROLE data_engineer;
GRANT ROLE data_engineer TO ROLE data_admin;

-- Schema-level permissions
GRANT USAGE ON SCHEMA analytics.marts TO ROLE data_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics.marts TO ROLE data_analyst;
```

---

## Cost Optimization

### Query Optimization

**Anti-patterns to Avoid:**
```sql
-- ❌ BAD: SELECT *
SELECT * FROM large_table;

-- ✅ GOOD: Select only needed columns
SELECT id, name, created_at FROM large_table;


-- ❌ BAD: Unrestricted JOINs
SELECT * FROM table_a JOIN table_b;

-- ✅ GOOD: Filter before joining
WITH filtered_a AS (
  SELECT * FROM table_a WHERE date > '2025-01-01'
)
SELECT * FROM filtered_a JOIN table_b USING (id);
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Data Freshness**
   - Last updated timestamp per model
   - Alert if >24 hours old

2. **Model Run Time**
   - Track dbt model execution duration
   - Alert on 2x slowdown

3. **Test Failure Rate**
   - % of tests failing
   - Alert on >5% failure rate

4. **Warehouse Credits**
   - Daily spend by warehouse
   - Alert on budget overruns

---

## Conclusion

A well-architected modern data stack should be:
- **Modular** - Clear layer separation
- **Testable** - Comprehensive quality checks
- **Documented** - Self-service friendly
- **Performant** - Optimized for scale
- **Governed** - Proper access controls

This architecture has successfully scaled from small teams to 200+ data consumers across multiple organizations.

---

*Questions or suggestions? Open an issue or PR!*