from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# ── Build the owner ───────────────────────────────────────────────────────────
owner = Owner(name="Jordan", contact="jordan@email.com")

# ── Create two pets ───────────────────────────────────────────────────────────
mochi = Pet(name="Mochi", species="cat", age=3)
boba  = Pet(name="Boba",  species="dog", age=5)

# ── Add tasks OUT OF ORDER (intentionally scrambled times) ───────────────────
mochi.add_task(Task(description="Dry food dinner",    time="18:00", frequency="daily",  priority="medium"))
mochi.add_task(Task(description="Refill water bowl",  time="07:00", frequency="daily",  priority="high"))
mochi.add_task(Task(description="Wet food breakfast", time="08:00", frequency="daily",  priority="high"))

boba.add_task(Task(description="Flea medication",     time="19:00", frequency="weekly", priority="low"))
boba.add_task(Task(description="Evening walk",        time="17:00", frequency="daily",  priority="high"))
boba.add_task(Task(description="Lunch kibble",        time="12:00", frequency="daily",  priority="medium"))
boba.add_task(Task(description="Morning walk",        time="07:30", frequency="daily",  priority="high"))

owner.add_pet(mochi)
owner.add_pet(boba)

scheduler = Scheduler(owner=owner)

# ── Helper: print a list of (Pet, Task) pairs ─────────────────────────────────
def print_tasks(pairs, label):
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    if not pairs:
        print("  (no tasks)")
        return
    for pet, task in pairs:
        status = f"done @ {task.completed_at.strftime('%H:%M')}" if task.completed else "pending"
        print(
            f"  [{task.priority.upper():6}] "
            f"{pet.name:6} | {task.due_date} | {task.time} | "
            f"{task.description} ({task.frequency}) — {status}"
        )

# ─────────────────────────────────────────────────────────────────────────────
# 1. sort_by_time — scrambled input, chronological output
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  DEMO 1: sort_by_time()")
print("=" * 60)
print("\n  Boba's tasks as added (out of order):")
for t in boba.tasks:
    print(f"    {t.time}  {t.description}")

print("\n  After sort_by_time():")
for t in scheduler.sort_by_time(boba.tasks):
    print(f"    {t.time}  {t.description}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. filter_by_pet and filter_by_status — baseline snapshot
# ─────────────────────────────────────────────────────────────────────────────
print_tasks(scheduler.filter_by_pet("Mochi"), "filter_by_pet('Mochi')")
print_tasks(scheduler.filter_by_pet("Boba"),  "filter_by_pet('Boba')")
print_tasks(scheduler.filter_by_status("pending"),   "filter_by_status('pending') — baseline")
print_tasks(scheduler.filter_by_status("completed"), "filter_by_status('completed') — baseline")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Recurring task auto-scheduling
#    Complete two tasks and confirm the next occurrence was created
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  DEMO 2: complete_task() auto-schedules next occurrence")
print("=" * 60)

today = date.today()
print(f"\n  Today is {today}")
print(f"  Mochi task count before: {len(mochi.tasks)}")
print(f"  Boba  task count before: {len(boba.tasks)}")

# Complete a daily task (Mochi) and a weekly task (Boba)
scheduler.complete_task("Mochi", "Refill water bowl")   # daily → +1 day
scheduler.complete_task("Boba",  "Flea medication")     # weekly → +7 days
scheduler.complete_task("Mochi", "Dry food dinner")     # daily → +1 day

print(f"\n  Mochi task count after:  {len(mochi.tasks)}  (was 3, +1 new daily instance)")
print(f"  Boba  task count after:  {len(boba.tasks)}  (was 4, +1 new weekly instance)")

# Show the newly created future instances
print("\n  Upcoming (future) task instances auto-created by next_occurrence():")
for pet in [mochi, boba]:
    for task in pet.tasks:
        if task.due_date > today:
            print(
                f"    {pet.name:6} | due {task.due_date} "
                f"(+{(task.due_date - today).days}d) | "
                f"{task.time} | {task.description} ({task.frequency})"
            )

# ─────────────────────────────────────────────────────────────────────────────
# 4. filter_by_status after completions — completed list now populated
# ─────────────────────────────────────────────────────────────────────────────
print_tasks(scheduler.filter_by_status("completed"), "filter_by_status('completed') — after 3 completions")
print_tasks(scheduler.filter_by_status("pending"),   "filter_by_status('pending')  — after 3 completions")

# ─────────────────────────────────────────────────────────────────────────────
# 5. filter_tasks — combined pet + time window
# ─────────────────────────────────────────────────────────────────────────────
print_tasks(
    scheduler.filter_tasks(pet_name="Boba", status="pending", time_before="13:00"),
    "filter_tasks(pet='Boba', status='pending', time_before='13:00')"
)

# ─────────────────────────────────────────────────────────────────────────────
# 6. conflict_warnings — same-pet and cross-pet
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  DEMO 3: conflict_warnings()")
print("=" * 60)

# ── Baseline: should be clean ─────────────────────────────────────────────────
print("\n  [a] Clean schedule — no conflicts expected:")
warnings = scheduler.conflict_warnings()
print(f"      {warnings if warnings else 'No conflicts detected.'}")

# ── Same-pet conflict: two tasks for Boba at 17:00 ───────────────────────────
print("\n  [b] Adding same-pet conflict — 'Vet appointment' for Boba @ 17:00")
print("      (Boba already has 'Evening walk' @ 17:00)")
scheduler.add_task("Boba", Task(description="Vet appointment", time="17:00", frequency="once", priority="high"))
for msg in scheduler.conflict_warnings():
    print(f"      {msg}")

# ── Cross-pet conflict: Mochi also gets a task at 07:30 (same as Boba's walk) ─
print("\n  [c] Adding cross-pet conflict — 'Groom' for Mochi @ 07:30")
print("      (Boba already has 'Morning walk' @ 07:30)")
scheduler.add_task("Mochi", Task(description="Groom session", time="07:30", frequency="once", priority="medium"))
for msg in scheduler.conflict_warnings():
    print(f"      {msg}")

print()
