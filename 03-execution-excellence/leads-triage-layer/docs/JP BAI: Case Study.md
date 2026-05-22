As mentioned during our first conversation, our ambition is to insulate 1.000.000 homes across Europe. To do that at scale, we want to become the first autonomous construction company, to reach this goal faster while earning the trust of the homeowners. Plenty of interesting challenges ahead, in software and in the real world.

#### Why this case study exists

AI-assisted coding has made standard take-homes pretty boring. A CRUD clone or leetcode puzzle won’t tell us what we actually would like to know: **how you think about a real business problem when the solution isn’t obvious.**

So we built something different. There’s no single correct answer here. Multiple defensible approaches exist. We’re looking for reasoning, trade-offs, and taste, not label-matching.

- **Walkthrough:** 40 minutes, on-site.
- **Time:** Plan for 4-8 hours of focused work.
- **Tools:** Use any LLM, any framework you like.
- **Stack:** Pick whatever helps you ship something. TypeScript, Python, whatever you need. We care about your thinking and reasoning, not your framework choice.

#### The business problem

ClimateTech insulates homes at scale across Germany. The funnel for this case study:

- **1.200-1.500** leads/month
- **52%** qualify past the initial phone call
- **≈12%** of leads become paying customers
- **20%** of installed projects surface issues in planning or on-site (cavity bigger than planned, scope misestimated, too little time planned, temperature too low)
- **€5.000** typical project deal value

As we scale, the bottleneck is shifting from sales capacity to decision quality: how well we triage, price, and brief.
A mispriced project eats margin. A bad sales-to-operations handoff turns a profitable project into rework. A missed disqualification wastes a colleagues ressources.

Over time we want to build an AI coordination system that treats every lead across its lifecycle as context-rich, not just a form submission with a few follow-up calls.

#### Your task

You’re building a **triage layer**.

For each new lead, your system receives:

- A structured intake JSON (what the rep captured on the call)
- The full transcript of the qualification call

Your system produces, per lead, three things:

1. **A triage decision:** we recommend `pitch` / `disqualify` / `escalate` / `pitch_with_flag` / `pitch_with_cross_sell`. If you design something different, walk us through why.
2. **A confidence score:** could be probabilistic, a 1–5 scale, or a category like `high` / `needs-review` / `low`. We want to see what “confidence” means in your design.
3. **A field briefing:** actionable notes for the sales reps follow-up video call. What to watch for, what similar past projects went wrong on, what to price carefully.

You’ll process **10 new leads** (in `data/new_leads/`). They range across baseline cases, edge cases, and things that look obvious but aren’t. Don’t over-index on getting every one “right”; focus on how your system behaves across the set.

#### What we give you

Everything below is in the **`climatetech-fse-case-study.zip`** attached to this page. Extract it and you’ll get this structure:

```
data/
  past_projects.jsonl           # 1,000 past projects, your system's memory
  new_leads/
    LEAD-XXX/
      intake.json               # structured CRM event
      transcript.md             # full call transcript (German)
    ... × 10

qualification_rules.md          # the rule-set our reps follow on the call
```

A note on `past_projects.jsonl`: this includes records at every funnel stage, not just installed projects. Every lead becomes a `project` record at creation; the `stage` field shows where it ended (disqualified at the call, quoted but lost, or signed and installed).

The data is **simulated** but built around ClimateTech’s funnel, process, regional rules, and common on-site issues. You’ll find realistic noise: some fields are missing, rep voices differ in quality, some call notes echo what’s in the structured intake and some don’t. That’s the job.

All transcripts and call summaries are in German. If that’s a challenge, please use an LLM, that’s part of the realism.

#### What you submit

1. **Working prototype:** a CLI or small HTTP endpoint that takes one lead (`intake.json` + `transcript.md`) and returns your triage output. Process all 10 leads through it so we can see the results. Share as a GitHub repo or zip. No UI needed.
2. **1-page decision log** (markdown):
    - What you built
    - What you deliberately didn’t build, and why
    - What you’d build later on
3. **The system’s output on all 10 leads**, in whatever format you designed.

#### Meeting @ ClimateTech

It should be more conversation than presentation. We’ll talk about the choices behind your work and the alternatives you ruled out.

**What we’re not focused on:**

- Perfect code style or test coverage
- UI polish (a CLI is fine)
    - “Correctly” handling every one of the 10 leads
- Fancy infra unless it actually earns its complexity

**What we are looking for:**

- Scoping: what you chose not to build
- Data literacy: do you trust the structured intake, or do you validate against the transcript?
- Judgment: where do you use deterministic logic vs. LLM reasoning, and why?
- Evaluation thinking: can you describe how you’d know this works in production?
- Your reasoning: every decision should have a “why” you can walk us through

#### General note

- **Submission deadline:** day before the meeting slot, let us know otherwise.
- **Stuck?** No problem, just get as far as you can.

#### **Attachment**

[climatetech-fse-case-study.zip](attachment:57d4e0cd-1f23-4462-8dca-5bd708cc8cbe:climatetech-fse-case-study.zip)

---

Good luck 🌞 We’re excited to see how you think.