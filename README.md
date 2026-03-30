# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The following algorithmic features were added to `Scheduler` in Module 2:

### Sort by time
`sort_by_time(tasks)` orders any list of `Task` objects chronologically using
Python's `sorted()` with a lambda key that parses each `"HH:MM"` string into a
`datetime`. Tasks with no fixed time (e.g. `"anytime"`) are pushed to the end
via `datetime.max`.

### Filter by pet or status
Three composable filter methods let callers slice the schedule without looping manually:

| Method | What it returns |
|---|---|
| `filter_by_pet(name)` | All tasks for one named pet, chronological |
| `filter_by_status(status)` | `"pending"` or `"completed"` tasks across all pets |
| `filter_tasks(pet, status, time_after, time_before)` | Any combination of the above plus a time window |

### Recurring task auto-scheduling
`Task.next_occurrence()` uses `datetime.timedelta` to calculate the next due
date for recurring tasks and returns a fresh, incomplete `Task` instance:

- `"daily"` / `"twice daily"` → `due_date + timedelta(days=1)`
- `"weekly"` → `due_date + timedelta(days=7)`
- `"once"` / `"as needed"` → returns `None` (no future instance created)

`Scheduler.complete_task()` calls this automatically — marking a recurring
task done immediately enqueues its next occurrence on the pet's task list.

### Conflict detection
`detect_conflicts()` scans for scheduling collisions keyed on `(due_date, time)`,
catching two kinds of overlap without raising exceptions:

- **Same-pet** — two tasks for one pet at the exact same time slot.
- **Cross-pet** — tasks for different pets at the same slot (the owner cannot
  attend both simultaneously).

`conflict_warnings()` wraps the results as plain warning strings, making it
safe to call from the UI at any time:

```python
for msg in scheduler.conflict_warnings():
    print(msg)
```

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
