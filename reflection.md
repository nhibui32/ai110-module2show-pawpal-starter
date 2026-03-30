# PawPal+ Project Reflection

## 1. System Design
- Add cat and owner information 
- track the walks 
- track if they eat, drink 
**a. Initial design**

The initial design used four classes to separate data from behavior:

- **Owner** — stores the pet owner's name and contact information. It is a simple data class with no logic; it exists so the app knows who is responsible for the pet.
- **Pet** — stores the animal's name and species, and holds a reference to its Owner. Its only responsibility is to represent the subject of all care activity.
- **Task** — represents a single care activity such as a walk, a meal, or a water check. It holds the task title, category, duration in minutes, priority level (low/medium/high), optional notes, and a completion flag with a timestamp. It is responsible for knowing its own state (pending vs. done) and for converting itself to a dictionary for display.
- **Scheduler** — the central coordinator. It holds a Pet and a list of Tasks. It is responsible for adding and removing tasks, marking tasks complete, sorting the task list by priority, and producing a human-readable daily summary.

**b. Design changes**

Yes, the design changed in two ways based on AI feedback during implementation:

1. **Added `category` to Task** — The initial idea was to track tasks only by title and priority. The AI suggested adding a `category` field (walk, eat, drink, medication, play, grooming) so tasks could be grouped and filtered by type. This made it easier to answer questions like "did the cat eat today?" without parsing free-text titles.

2. **Moved completion tracking into Task instead of Scheduler** — Originally the plan was to have the Scheduler maintain a separate log of completed task titles. The AI pointed out that storing `completed` and `completed_at` directly on the Task object keeps each task self-contained and makes it simpler to display status in the UI table. The Scheduler then only needs to filter `task.completed` rather than cross-reference a separate list.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints, applied in this order of importance:

1. **Completion status** — incomplete tasks always appear before done ones. A
   pet owner's primary question is "what still needs doing today?", so surfacing
   pending work first is the most valuable thing the scheduler can do.

2. **Scheduled time** — within the pending group, tasks are sorted chronologically
   by their `"HH:MM"` attribute using `_parse_time()`. Time order matters more
   than priority because a high-priority task at 18:00 cannot be acted on before
   a medium-priority task at 07:00.

3. **Priority** — used as a tiebreaker when two tasks share the same time slot.
   High-priority tasks (numeric value 3) rise above medium (2) and low (1).

Completion status was chosen as the top constraint because the UI's main job is
to answer "what's left?" — not to rank things the owner already finished. Time
was chosen over priority because pet care is time-driven: medications have
specific windows, walks follow routines. Priority only matters when two things
compete for the same moment.

**b. Tradeoffs**

**Tradeoff: exact time-slot matching instead of overlapping duration windows**

The `detect_conflicts()` method flags a conflict only when two tasks share the
exact same `"HH:MM"` string on the same `due_date`. It does not consider how
long each task takes — a 5-minute water refill and a 90-minute vet trip both
occupy a single timestamp, so two tasks at `"08:00"` and `"09:00"` are never
flagged even if the first one realistically runs into the second.

*Why this tradeoff is reasonable here:*

1. **Tasks have no `duration` field.** Adding duration would require every
   task to carry an extra attribute, every form in the UI to collect it, and
   every sort/filter to account for overlapping intervals — a significant
   increase in complexity for an introductory scheduling app.

2. **Exact matches catch the most obvious scheduling mistakes.** A pet owner
   who accidentally books a vet appointment at the same time as the morning
   walk gets an immediate warning without any extra data entry.

3. **The fix is additive, not structural.** If duration support is needed
   later, `Task` can gain an optional `duration_minutes: int = 0` field, and
   `detect_conflicts()` can be updated to check for interval overlap
   (`start < other_end and end > other_start`) without changing any other
   method or the UI layout.

*What it costs:* back-to-back tasks like a 60-minute walk at `"07:30"`
followed by a vet at `"08:00"` will not be flagged, even though a real owner
would need to leave for the vet before finishing the walk. The scheduler
silently trusts the owner to leave enough buffer between appointments.

*AI simplification note (reviewed during Module 2):* When asked to simplify
`filter_by_status()`, the AI suggested replacing the explicit `if/elif/else`
block with a dict of lambdas and a single `.get()` call. That version is
shorter but requires the reader to unpack three levels of indirection (dict →
lambda → comprehension condition) before understanding the intent. The
explicit version was kept because readability outweighs brevity in a codebase
where the logic should be self-documenting.

---

## 3. AI Collaboration

**a. How you used AI**

AI tools were used across four distinct phases:

- **Algorithm brainstorming** — using `#codebase` context to ask which sorting
  and filtering improvements would benefit a pet scheduling app. This produced a
  prioritized list of four features (time sorting, status/pet filtering, recurring
  tasks, conflict detection) that became the Module 2 roadmap.

- **Inline code generation** — Copilot Inline Chat was used to draft the initial
  body of `sort_by_time()`, `filter_by_status()`, and `detect_conflicts()`. The
  drafts were always reviewed and often restructured before being kept.

- **Test generation** — Chat was asked "what are the most important edge cases
  for a scheduler with sorting and recurring tasks?" to build a test plan, then
  individual test functions were drafted from that plan.

- **Simplification review** — a completed method (`filter_by_status`) was shared
  with Chat and asked "how could this be simplified for readability or
  performance?" to deliberately stress-test the design.

The most useful prompt pattern was providing *context + constraint*: instead of
"write a filter function," asking "write a filter function that returns (Pet, Task)
pairs, never raises, and sorts results chronologically." Specificity produced
usable first drafts rather than generic code that required heavy rewriting.

**b. Judgment and verification**

The clearest rejection was the `filter_by_status()` simplification suggestion.
When asked for a more idiomatic Python version, AI proposed:

```python
filters = {"pending": lambda t: not t.completed, "completed": lambda t: t.completed}
condition = filters.get(status, lambda t: True)
filtered = [(p, t) for p, t in all_tasks if condition(t)]
```

This was evaluated by asking: "can a classmate reading this for the first time
understand what it does in under ten seconds?" The answer was no — a reader has
to mentally unwrap the dict lookup, then realize `.get()` falls back to a lambda
that always returns True, then trace how that lambda feeds the comprehension
condition. The explicit `if / else if / else` block names each case directly and is
immediately readable. The AI version was rejected and the original kept.

Verification approach: whenever AI generated a non-trivial algorithm, a
corresponding unit test was written *before* accepting the code. If the test
passed on the first run without any changes to the implementation, that was a
signal the AI draft was structurally correct. If it failed, the bug was
diagnosed before modifying anything, to distinguish "wrong test assumption" from
"wrong implementation" — as happened with `test_completing_already_done_task_does_not_duplicate`.

---

## 4. Testing and Verification

**a. What you tested**

The 31-test suite in `tests/test_pawpal.py` covered six areas:

1. **Sorting** — tasks added in scrambled time order must come back chronological;
   `"anytime"` tasks must sort last; pending tasks must appear before completed ones.
   These tests matter because an owner who sees tasks out of order might miss a
   time-sensitive medication or walk.

2. **Recurrence** — `next_occurrence()` must produce a task dated `+1 day` for
   daily frequency and `+7 days` for weekly; `"once"` and `"as needed"` must
   return `None`. Without these tests a silent off-by-one in the `timedelta` math
   would schedule tomorrow's task for the wrong day with no visible error.

3. **Conflict detection** — both same-pet and cross-pet collisions must be
   flagged; a clean schedule must return an empty list; recurring next-occurrence
   copies on future dates must not produce false positives. The false-positive test
   was added after discovering the `(due_date, time)` key fix was necessary.

4. **Filters** — each filter method must narrow results correctly and return empty
   for unknown inputs without crashing. These tests protect the UI layer, which
   calls filters on every page refresh.

5. **Edge cases** — a pet with zero tasks, completing a `"once"` task twice,
   calling `complete_task()` for a non-existent pet or description. Edge cases
   are important because the Streamlit session can get into unusual states if a
   user removes a pet after adding tasks.

**b. Confidence**

★★★★☆ (4 / 5)

High confidence in the core scheduling logic — every algorithm added in Module 2
has direct test coverage and all 31 tests pass consistently in under 0.05 seconds.
Confidence is not 5 stars because two areas remain untested:

- **Persistence** — data lives only in `st.session_state`; a page refresh wipes
  everything. There are no tests verifying that state survives a Streamlit rerun.
- **UI layer** — `app.py` is not covered by any automated test. A broken widget
  label or a missing `st.rerun()` call would only surface through manual testing.

Next edge cases to test if time allowed:
- Adding 100+ tasks to one pet and verifying sort performance stays fast.
- `reset_daily_tasks()` leaves `"once"` tasks completed and resets `"daily"` ones.
- `filter_tasks()` with all four parameters set simultaneously.

---

## 5. Reflection

**a. What went well**

The most satisfying part is the recurring task auto-scheduling. The decision to
put `next_occurrence()` on the `Task` class itself — rather than in the
`Scheduler` — meant that `complete_task()` only needed one extra line
(`pet.add_task(next_task)`) to gain the entire feature. The class boundary was
correct from the start: a `Task` knows its own frequency and how to clone itself
for the next date; the `Scheduler` just acts on what the `Task` returns.

The test suite catching the false-positive conflict bug (recurring copies flagging
against today's completed instance) was also a win — that bug would have been
invisible to manual testing because the warning only appears when conflicts exist.

**b. What you would improve**

Two things would be redesigned in a next iteration:

1. **Date-aware `complete_task()`** — currently `complete_task("Rex", "Morning walk")`
   completes whichever pending instance it finds first, regardless of `due_date`.
   This means calling it twice in one session completes today's task and then
   immediately completes tomorrow's auto-created copy. A `due_date` parameter
   would make the method explicit: `complete_task("Rex", "Morning walk", date.today())`.

2. **Persistent storage** — replacing `st.session_state` with a lightweight local
   database (SQLite via `sqlite3` or a JSON file) would let the schedule survive
   page refreshes and browser restarts, which is the most common complaint a real
   user would have with the current app.

**c. Key takeaway**

The most important thing learned was that **AI is a fast first-draft generator,
not a decision-maker**. Every useful contribution from Copilot came when it was
given a specific contract to implement: inputs, outputs, constraints, and what
"correct" looks like. When asked open-ended questions it produced plausible code
that needed architectural review before it could be trusted.

The moment that made this clearest was the `filter_by_status()` simplification:
the AI's version was shorter and would have passed every test, but it made the
code harder for a human to read and maintain. Choosing to reject it required
understanding *why* the original was written the way it was — which is exactly
the kind of judgment that belongs to the lead architect, not the AI assistant.
Working with AI well means staying in that role: setting the constraints,
reviewing the output, and being willing to say no.
