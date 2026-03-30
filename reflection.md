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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
