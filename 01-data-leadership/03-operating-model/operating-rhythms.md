# Data Team Operating Model

**How I establish rhythms and rituals that enable scale.**

This document outlines the operating cadences, processes, and frameworks I implement when building or leading data teams. These practices create predictability, transparency, and stakeholder trust.

---

## Weekly Rhythms

### 1. Stakeholder Sync (30 min)
**Attendees**: Data team + key business stakeholders (rotating by domain)

**Agenda**:
- **Wins** (5 min): What shipped this week? What insights drove decisions?
- **Blockers** (5 min): What's preventing progress? Decisions needed?
- **Upcoming** (10 min): What's landing next week? Stakeholder input needed?
- **Feedback** (10 min): What's working? What's not?

**Purpose**: Build partnership, surface issues early, maintain transparency

---

### 2. Team Standup (15 min)
**Attendees**: Data team only

**Format**: 
- What did I complete yesterday?
- What am I working on today?
- What blockers do I need help with?

**Rules**:
- Keep it brief—deep dives happen offline
- Celebrate wins publicly
- Blockers get immediate follow-up

---

### 3. Deep Work Block (Half-day)
**No meetings, no Slack urgency**

Data work requires focus. I protect at least one half-day per week for the team to do uninterrupted work—complex modeling, architecture decisions, or catching up on technical debt.

---

## Bi-Weekly Rhythms

### 1. Sprint Planning (60 min)
**Attendees**: Data team + relevant stakeholders

**Format**:
- Review completed work from previous sprint
- Prioritize upcoming work using MoSCoW framework
- Assign owners and define "done" for each item
- Identify dependencies and risks

**Input**: Prioritized backlog (maintained in NOW/NEXT/LATER format)

---

### 2. 1-on-1s (30 min per person)
**Private coaching and development conversations**

**Topics**:
- Progress on personal goals
- Skill development and growth
- Feedback (both directions)
- Career trajectory discussions
- Workload and wellbeing check

---

### 3. Code Review Session (60 min)
**Optional deep dive into significant technical decisions**

Not every PR requires group review, but major architectural changes or complex models benefit from collaborative input. This also serves as learning opportunity for junior team members.

---

## Monthly Rhythms

### 1. Team Retrospective (60 min)
**Continuous improvement for team processes**

**Format**:
- What went well? (10 min)
- What could be better? (15 min)
- What will we change? (15 min)
- Action items assigned (20 min)

**Output**: Documented process changes, owner assignments

---

### 2. Stakeholder Satisfaction Review (30 min)
**Are we delivering value?**

**Metrics to review**:
- Dashboard usage analytics
- Request volume trends
- Qualitative feedback from key partners
- Time-to-delivery for common request types

---

### 3. Data Quality Review (30 min)
**Are we maintaining trust?**

**Agenda**:
- Review test failure trends
- Discuss any data incidents and root causes
- Update monitoring thresholds if needed
- Plan quality improvement initiatives

---

## Quarterly Rhythms

### 1. Roadmap Planning (2-3 hours)
**Strategic alignment with business priorities**

**Process**:
1. Review business OKRs and strategic initiatives
2. Map data initiatives to business goals
3. Estimate capacity and identify hiring needs
4. Define success metrics for each major initiative
5. Communicate roadmap to stakeholders

**Output**: Quarterly roadmap document, shared with leadership

---

### 2. Team Offsite or Team Building (Half-day)
**Strengthen relationships and step back from day-to-day**

**Activities**:
- Team health check (psychological safety assessment)
- Skill sharing session (one team member teaches the group)
- Strategic brainstorming ("What should we start/stop/continue?")
- Social time (team bonding)

---

### 3. Performance Calibration (Leadership only)
**Ensure fair and consistent performance management**

Review team member progress against growth frameworks, adjust leveling, and plan compensation conversations.

---

## Request Intake Process

### 1. Request Submission
Stakeholders submit requests through a standard template:

```
**Requester**: Name and team
**Business Problem**: What decision does this inform?
**Success Criteria**: How will we know this is done?
**Urgency**: Business impact if not delivered this quarter
**Data Sources**: What systems do you think we need?
**Stakeholders**: Who else needs to see this?
```

### 2. Prioritization Framework
I use **MoSCoW** for categorization:

- **Must Have**: Critical business metrics, regulatory requirements, blocking other work
- **Should Have**: Important insights that improve decisions but aren't blocking
- **Could Have**: Nice-to-have enhancements or experimental work
- **Won't Have**: Out of scope (documented for future consideration)

### 3. Capacity Planning
**NOW/NEXT/LATER** backlog management:

- **NOW**: Current sprint (locked, rarely changes)
- **NEXT**: Planned for upcoming sprint (prioritized, may change based on urgency)
- **LATER**: Backlog (unprioritized, reviewed monthly)

### 4. SLA Communication
Clear expectations for different request types:

| Request Type | Response Time | Delivery Time |
|-------------|---------------|---------------|
| Bug/Blocker | 24 hours | 48-72 hours |
| Quick Win (<4 hours) | 48 hours | Within current sprint |
| Standard Request | 1 week | Within 2 sprints |
| Major Initiative | 2 weeks | Roadmap planning |

---

## Definition of Done

For any data product (dashboard, model, analysis), "done" means:

1. **Code**: Written, tested, reviewed, merged
2. **Documentation**: Model docs, business logic explained, usage guide if applicable
3. **Quality**: dbt tests passing, data freshness monitored
4. **Stakeholder Sign-off**: Reviewed with requester, meets success criteria
5. **Knowledge Transfer**: Team demo or documentation for maintainers

---

## Communication Norms

### Slack Guidelines
- **Threads**: Use threads for discussions to keep channels clean
- **Urgency Tags**: 
  - No tag = Normal priority (response within business hours)
  - `@here` = Needs attention today
  - `@channel` = Urgent, everyone should see
- **Decisions**: Document in Confluence/Notion, link in Slack
- **Wins**: Celebrate publicly, tag relevant stakeholders

### Meeting Guidelines
- **Agenda Required**: Every meeting has an agenda or it's cancelled
- **Action Items**: Documented and assigned before meeting ends
- **Optional by Default**: Unless explicitly marked required, attendance is optional
- **Recordings**: Available for async review (when appropriate)

### Documentation Standards
- **Single Source of Truth**: One place for each type of info
  - Technical docs: dbt docs / Confluence
  - Business context: Confluence / Notion
  - Runbooks: Confluence / GitHub
  - Code: GitHub with READMEs
- **Living Documents**: Updated as things change, not after
- **Discoverability**: Clear naming, logical structure, cross-linking

---

## Incident Response Protocol

### Severity Levels

**P1 (Critical)**: Data outage affecting business operations
- Response: Immediate
- Communication: Within 30 min to stakeholders
- Resolution: All hands until resolved

**P2 (High)**: Significant data quality issue affecting trust
- Response: Within 4 hours
- Communication: Within 2 hours to affected stakeholders
- Resolution: Prioritized above normal sprint work

**P3 (Medium)**: Minor data issue or single stakeholder impact
- Response: Within 24 hours
- Communication: Standard stakeholder update
- Resolution: Prioritized in next sprint

### Post-Incident Review
Within 48 hours of resolution:
- What happened?
- Why did it happen? (Root cause, not blame)
- What did we learn?
- What will we change to prevent recurrence?

---

## Why This Matters

Operating models aren't bureaucracy—they're **enabling constraints** that:

1. **Reduce Decision Fatigue**: Clear processes mean less time deciding how to work
2. **Increase Predictability**: Stakeholders know what to expect and when
3. **Enable Scale**: Documented practices allow new team members to onboard quickly
4. **Build Trust**: Transparency and consistency create stakeholder confidence
5. **Protect Team Health**: Boundaries prevent burnout and enable sustainable pace

I've refined this model across multiple organizations. It should always be adapted to context—but starting with clear structure is easier than adding it later.
