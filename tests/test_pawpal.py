"""
Automated test suite for PawPal+ — pawpal_system.py

Coverage areas
--------------
1. Existing baseline  — mark_complete, add_task
2. Sorting            — sort_by_time, get_schedule
3. Recurrence         — next_occurrence, complete_task auto-scheduling
4. Conflict detection — detect_conflicts, conflict_warnings
5. Filters            — filter_by_pet, filter_by_status, filter_tasks
6. Edge cases         — empty pet, already-done task, "once" frequency
"""
# ruff: noqa: S101

from datetime import date, timedelta
import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures — shared setup reused across tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def basic_pet():
    """A single pet with no tasks — used for edge-case tests."""
    return Pet(name="Luna", species="cat", age=2)


@pytest.fixture
def scheduler_two_pets():
    """
    Scheduler with two pets (Rex and Luna) and a handful of tasks added
    deliberately out of chronological order.
    """
    owner = Owner(name="Jordan")
    rex  = Pet(name="Rex",  species="dog", age=4)
    luna = Pet(name="Luna", species="cat", age=2)

    # Rex — added out of order
    rex.add_task(Task(description="Evening walk",   time="17:00", frequency="daily",  priority="high"))
    rex.add_task(Task(description="Morning walk",   time="07:30", frequency="daily",  priority="high"))
    rex.add_task(Task(description="Lunch kibble",   time="12:00", frequency="daily",  priority="medium"))
    rex.add_task(Task(description="Flea treatment", time="19:00", frequency="weekly", priority="low"))
    # Tasks above are intentionally added out of chronological order to verify sorting.

    # Luna — added out of order
    luna.add_task(Task(description="Wet food dinner",    time="18:00", frequency="daily", priority="medium"))
    luna.add_task(Task(description="Refill water bowl",  time="07:00", frequency="daily", priority="high"))
    luna.add_task(Task(description="Wet food breakfast", time="08:00", frequency="daily", priority="high"))

    owner.add_pet(rex)
    owner.add_pet(luna)
    return Scheduler(owner=owner)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Baseline (pre-existing behaviours)
# ─────────────────────────────────────────────────────────────────────────────

def test_mark_complete_changes_status():
    """Task.mark_complete() should flip completed to True and record a timestamp."""
    task = Task(description="Morning walk", time="07:30", frequency="daily", priority="high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True
    assert task.completed_at is not None


def test_add_task_increases_pet_task_count(basic_pet):
    """Pet.add_task() should increase the pet's task list by exactly one."""
    assert len(basic_pet.tasks) == 0
    basic_pet.add_task(Task(description="Refill water bowl", time="07:00",
                            frequency="daily", priority="high"))
    assert len(basic_pet.tasks) == 1


# ─────────────────────────────────────────────────────────────────────────────
# 2. Sorting
# ─────────────────────────────────────────────────────────────────────────────

def test_sort_by_time_chronological(scheduler_two_pets):
    """sort_by_time() must return tasks earliest-first regardless of insertion order."""
    rex = scheduler_two_pets.owner.get_pet("Rex")
    sorted_tasks = scheduler_two_pets.sort_by_time(rex.tasks)
    times = [t.time for t in sorted_tasks]
    assert times == sorted(times), f"Expected chronological order, got {times}"


def test_sort_by_time_anytime_last(scheduler_two_pets):
    """Tasks with time='anytime' must sort to the end of the list."""
    pet = scheduler_two_pets.owner.get_pet("Luna")
    pet.add_task(Task(description="Play session", time="anytime", frequency="as needed", priority="low"))
    sorted_tasks = scheduler_two_pets.sort_by_time(pet.tasks)
    assert sorted_tasks[-1].time == "anytime"


def test_get_schedule_pending_before_completed(scheduler_two_pets):
    """get_schedule() must list all pending tasks before any completed tasks."""
    scheduler_two_pets.complete_task("Rex", "Morning walk")
    schedule = scheduler_two_pets.get_schedule()
    completed_indices = [i for i, (_, t) in enumerate(schedule) if t.completed]
    pending_indices   = [i for i, (_, t) in enumerate(schedule) if not t.completed]
    if completed_indices and pending_indices:
        assert max(pending_indices) < min(completed_indices), (
            "A completed task appeared before a pending task in get_schedule()"
        )


def test_get_schedule_sorted_by_time_within_pending(scheduler_two_pets):
    """Within the pending group, tasks must be in chronological time order."""
    pending = [(p, t) for p, t in scheduler_two_pets.get_schedule() if not t.completed]
    times = [t.time for _, t in pending]
    assert times == sorted(times), f"Pending tasks not in time order: {times}"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Recurrence — next_occurrence and complete_task auto-scheduling
# ─────────────────────────────────────────────────────────────────────────────

def test_daily_task_next_occurrence_is_tomorrow():
    """next_occurrence() for a daily task must be due exactly 1 day later."""
    today = date.today()
    task = Task(description="Feed", time="07:00", frequency="daily", priority="high", due_date=today)
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.due_date == today + timedelta(days=1)


def test_weekly_task_next_occurrence_is_seven_days():
    """next_occurrence() for a weekly task must be due exactly 7 days later."""
    today = date.today()
    task = Task(description="Flea treatment", time="19:00", frequency="weekly", priority="low", due_date=today)
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.due_date == today + timedelta(days=7)


def test_once_task_has_no_next_occurrence():
    """next_occurrence() must return None for a one-time task."""
    task = Task(description="Vet visit", time="10:00", frequency="once", priority="high")
    assert task.next_occurrence() is None


def test_as_needed_task_has_no_next_occurrence():
    """next_occurrence() must return None for an 'as needed' task."""
    task = Task(description="Brush teeth", time="anytime", frequency="as needed", priority="low")
    assert task.next_occurrence() is None


def test_complete_task_creates_next_occurrence_for_daily(scheduler_two_pets):
    """Completing a daily task must add exactly one new pending instance to the pet."""
    rex = scheduler_two_pets.owner.get_pet("Rex")
    count_before = len(rex.tasks)

    scheduler_two_pets.complete_task("Rex", "Morning walk")

    assert len(rex.tasks) == count_before + 1
    # The new task is incomplete and due tomorrow
    tomorrow = date.today() + timedelta(days=1)
    future_tasks = [t for t in rex.tasks if t.due_date == tomorrow and t.description == "Morning walk"]
    assert len(future_tasks) == 1
    assert future_tasks[0].completed is False


def test_complete_task_creates_next_occurrence_for_weekly(scheduler_two_pets):
    """Completing a weekly task must schedule a new instance 7 days out."""
    rex = scheduler_two_pets.owner.get_pet("Rex")
    scheduler_two_pets.complete_task("Rex", "Flea treatment")
    in_7_days = date.today() + timedelta(days=7)
    future = [t for t in rex.tasks if t.due_date == in_7_days and t.description == "Flea treatment"]
    assert len(future) == 1


def test_next_occurrence_inherits_same_attributes():
    """The next occurrence must copy description, time, frequency, and priority unchanged."""
    task = Task(description="Evening walk", time="17:00", frequency="daily", priority="high")
    nxt = task.next_occurrence()
    assert nxt.description == task.description
    assert nxt.time        == task.time
    assert nxt.frequency   == task.frequency
    assert nxt.priority    == task.priority
    assert nxt.completed   is False
    assert nxt.completed_at is None


# ─────────────────────────────────────────────────────────────────────────────
# 4. Conflict detection
# ─────────────────────────────────────────────────────────────────────────────

def test_no_conflicts_on_clean_schedule(scheduler_two_pets):
    """A freshly built schedule with no time collisions must return an empty conflict list."""
    assert scheduler_two_pets.detect_conflicts() == []


def test_same_pet_conflict_detected(scheduler_two_pets):
    """Adding a second task for Rex at 07:30 must produce a same-pet conflict."""
    scheduler_two_pets.add_task(
        "Rex",
        Task(description="Vet appointment", time="07:30", frequency="once", priority="high")
    )
    conflicts = scheduler_two_pets.detect_conflicts()
    same_pet = [c for c in conflicts if c["scope"] == "same-pet"]
    assert len(same_pet) == 1
    assert same_pet[0]["time"] == "07:30"
    assert "Rex" in same_pet[0]["pets"]


def test_cross_pet_conflict_detected(scheduler_two_pets):
    """Adding a Luna task at Rex's 07:30 slot must produce a cross-pet conflict."""
    scheduler_two_pets.add_task(
        "Luna",
        Task(description="Groom session", time="07:30", frequency="once", priority="medium")
    )
    conflicts = scheduler_two_pets.detect_conflicts()
    cross = [c for c in conflicts if c["scope"] == "cross-pet"]
    assert len(cross) == 1
    assert "Rex" in cross[0]["pets"]
    assert "Luna" in cross[0]["pets"]


def test_conflict_warnings_returns_strings(scheduler_two_pets):
    """conflict_warnings() must return a list of strings and never raise."""
    scheduler_two_pets.add_task(
        "Rex",
        Task(description="Vet appointment", time="07:30", frequency="once", priority="high")
    )
    warnings = scheduler_two_pets.conflict_warnings()
    assert isinstance(warnings, list)
    assert all(isinstance(w, str) for w in warnings)


def test_conflict_warnings_empty_when_no_conflicts(scheduler_two_pets):
    """conflict_warnings() must return [] when the schedule is clean."""
    assert scheduler_two_pets.conflict_warnings() == []


def test_conflicts_keyed_by_due_date(scheduler_two_pets):
    """Recurring next-occurrence copies on different dates must NOT conflict with today's tasks."""
    # Complete morning walk → creates tomorrow's instance at the same time
    scheduler_two_pets.complete_task("Rex", "Morning walk")
    conflicts = scheduler_two_pets.detect_conflicts()
    # The future copy (tomorrow) should not flag against today's completed instance
    assert conflicts == [], f"False-positive conflicts detected: {conflicts}"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Filters
# ─────────────────────────────────────────────────────────────────────────────

def test_filter_by_pet_returns_only_that_pets_tasks(scheduler_two_pets):
    """filter_by_pet() must return only (Pet, Task) pairs for the named pet."""
    results = scheduler_two_pets.filter_by_pet("Rex")
    assert all(p.name == "Rex" for p, _ in results)


def test_filter_by_pet_unknown_name_returns_empty(scheduler_two_pets):
    """filter_by_pet() must return [] for a pet name that does not exist."""
    assert scheduler_two_pets.filter_by_pet("Ghost") == []


def test_filter_by_pet_case_insensitive(scheduler_two_pets):
    """filter_by_pet() must match regardless of capitalization."""
    upper = scheduler_two_pets.filter_by_pet("REX")
    lower = scheduler_two_pets.filter_by_pet("rex")
    assert len(upper) == len(lower) > 0


def test_filter_by_status_pending(scheduler_two_pets):
    """filter_by_status('pending') must return only incomplete tasks."""
    scheduler_two_pets.complete_task("Rex", "Morning walk")
    results = scheduler_two_pets.filter_by_status("pending")
    assert all(not t.completed for _, t in results)


def test_filter_by_status_completed(scheduler_two_pets):
    """filter_by_status('completed') must return only finished tasks."""
    scheduler_two_pets.complete_task("Rex", "Morning walk")
    scheduler_two_pets.complete_task("Luna", "Refill water bowl")
    results = scheduler_two_pets.filter_by_status("completed")
    assert all(t.completed for _, t in results)
    assert len(results) == 2


def test_filter_tasks_combined_pet_and_status(scheduler_two_pets):
    """filter_tasks() with pet_name + status must narrow results to that pet's pending tasks."""
    scheduler_two_pets.complete_task("Rex", "Morning walk")
    results = scheduler_two_pets.filter_tasks(pet_name="Rex", status="pending")
    assert all(p.name == "Rex" and not t.completed for p, t in results)


def test_filter_tasks_time_window(scheduler_two_pets):
    """filter_tasks() with time_after/time_before must exclude tasks outside the window."""
    from pawpal_system import _parse_time
    results = scheduler_two_pets.filter_tasks(time_after="10:00", time_before="15:00")
    for _, t in results:
        assert _parse_time("10:00") <= _parse_time(t.time) <= _parse_time("15:00")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Edge cases
# ─────────────────────────────────────────────────────────────────────────────

def test_pet_with_no_tasks_returns_empty_schedule(basic_pet):
    """A pet with zero tasks must produce no entries in filters or schedules."""
    owner = Owner(name="Jordan")
    owner.add_pet(basic_pet)
    s = Scheduler(owner=owner)
    assert s.get_schedule() == []
    assert s.get_pending_tasks() == []
    assert s.filter_by_pet("Luna") == []
    assert s.filter_by_status("pending") == []
    assert s.detect_conflicts() == []


def test_completing_once_task_twice_does_not_duplicate(scheduler_two_pets):
    """
    Completing a 'once' task twice must not create any next-occurrence instances.
    The second call must return False because no pending instance remains.

    Note: for recurring tasks ('daily', 'weekly') the second call correctly
    completes the auto-created next-occurrence copy — that is expected behavior.
    This test isolates the 'once' case where no future instance is ever created.
    """
    scheduler_two_pets.add_task(
        "Rex",
        Task(description="One-time vet visit", time="10:00", frequency="once", priority="high")
    )
    rex = scheduler_two_pets.owner.get_pet("Rex")
    count_before = len(rex.tasks)

    first = scheduler_two_pets.complete_task("Rex", "One-time vet visit")
    assert first is True
    assert len(rex.tasks) == count_before   # no next occurrence added for "once"

    second = scheduler_two_pets.complete_task("Rex", "One-time vet visit")
    assert second is False                  # no pending instance left to complete
    assert len(rex.tasks) == count_before   # still no extra task added


def test_complete_task_unknown_pet_returns_false(scheduler_two_pets):
    """complete_task() for a non-existent pet must return False without crashing."""
    result = scheduler_two_pets.complete_task("Ghost", "Morning walk")
    assert result is False


def test_complete_task_unknown_description_returns_false(scheduler_two_pets):
    """complete_task() for a task description that doesn't exist must return False."""
    result = scheduler_two_pets.complete_task("Rex", "Nonexistent task")
    assert result is False


def test_filter_by_status_unknown_value_returns_all(scheduler_two_pets):
    """filter_by_status() with an unrecognized value must return all tasks unchanged."""
    all_tasks = scheduler_two_pets.owner.all_tasks()
    result = scheduler_two_pets.filter_by_status("unknown_status")
    assert len(result) == len(all_tasks)
