"""
PawPal+ Logic Layer — pawpal_system.py

Class hierarchy
---------------
Owner
  └── has many Pets
        └── each Pet has many Tasks

Scheduler
  └── receives an Owner, walks the hierarchy to retrieve all Tasks
"""

from datetime import date, datetime, timedelta
from typing import Optional


def _parse_time(t: str) -> datetime:
    """Convert 'HH:MM' to a datetime for comparison; push blank/None to end."""
    try:
        return datetime.strptime(t, "%H:%M")
    except (ValueError, TypeError):
        return datetime.max


# ─────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────

class Task:
    """
    A single pet-care activity.

    Attributes
    ----------
    description : str
        What needs to happen (e.g. "Morning walk", "Refill water bowl").
    time : str
        Suggested time of day, e.g. "08:00" or "morning".
    frequency : str
        How often this task recurs: "once", "daily", "twice daily", etc.
    priority : str
        "high", "medium", or "low".
    completed : bool
        Whether the task has been marked done today.
    completed_at : datetime | None
        Timestamp set when mark_complete() is called.
    """

    FREQUENCIES = {"once", "daily", "twice daily", "weekly", "as needed"}
    PRIORITIES = {"high": 3, "medium": 2, "low": 1}

    # How many days ahead each recurring frequency schedules its next instance.
    # timedelta(days=N) shifts a date forward by exactly N days:
    #   date.today() + timedelta(days=1)  →  tomorrow
    #   date.today() + timedelta(days=7)  →  one week from today
    _RECURRENCE_DAYS: dict[str, int] = {
        "daily":       1,
        "twice daily": 1,   # next same-time slot is tomorrow
        "weekly":      7,
    }

    def __init__(
        self,
        description: str,
        time: str = "anytime",
        frequency: str = "daily",
        priority: str = "medium",
        due_date: Optional[date] = None,
    ):
        """Initialize a Task with description, scheduled time, frequency, and priority."""
        self.description = description
        self.time = time
        self.frequency = frequency if frequency in self.FREQUENCIES else "daily"
        self.priority = priority if priority in self.PRIORITIES else "medium"
        self.completed: bool = False
        self.completed_at: Optional[datetime] = None
        # due_date tells us which calendar day this instance belongs to.
        # Defaults to today so existing call-sites need no changes.
        self.due_date: date = due_date if due_date is not None else date.today()

    def mark_complete(self) -> None:
        """Mark this task as done and record the timestamp."""
        self.completed = True
        self.completed_at = datetime.now()

    def next_occurrence(self) -> Optional["Task"]:
        """
        Return a fresh, incomplete Task instance scheduled for the next
        occurrence of this recurring task, or None for one-time tasks.

        How timedelta works here
        ------------------------
        timedelta(days=N) represents a duration of N days.  Adding it to a
        date object produces a new date exactly N days in the future:

            next_date = self.due_date + timedelta(days=days_ahead)
            #                          ^─────────────────────────^
            #                          e.g. timedelta(days=1) = +1 day
            #                               timedelta(days=7) = +1 week

        The new Task is a copy of this one with:
        - completed / completed_at reset to their initial values
        - due_date set to the calculated next date
        """
        days_ahead = self._RECURRENCE_DAYS.get(self.frequency)
        if days_ahead is None:
            return None  # "once" or "as needed" — no next occurrence

        next_date = self.due_date + timedelta(days=days_ahead)
        return Task(
            description=self.description,
            time=self.time,
            frequency=self.frequency,
            priority=self.priority,
            due_date=next_date,
        )

    def priority_value(self) -> int:
        """Return numeric priority so tasks can be sorted."""
        return self.PRIORITIES[self.priority]

    def reset(self) -> None:
        """Clear completion status for a new day."""
        self.completed = False
        self.completed_at = None

    def to_dict(self) -> dict:
        """Return task fields as a flat dictionary suitable for display in a table."""
        return {
            "description": self.description,
            "due date": self.due_date.strftime("%Y-%m-%d"),
            "time": self.time,
            "frequency": self.frequency,
            "priority": self.priority,
            "completed": "Yes" if self.completed else "No",
            "completed at": self.completed_at.strftime("%H:%M") if self.completed_at else "—",
        }

    def __repr__(self) -> str:
        """Return a concise string representation of the task for debugging."""
        status = "done" if self.completed else "pending"
        return f"Task({self.description!r}, {self.time}, {self.frequency}, {status})"


# ─────────────────────────────────────────────
# Pet
# ─────────────────────────────────────────────

class Pet:
    """
    Stores pet details and owns a list of Tasks.

    Attributes
    ----------
    name    : str
    species : str   e.g. "cat", "dog"
    age     : int   years
    tasks   : list[Task]
    """

    def __init__(self, name: str, species: str, age: int = 0):
        """Initialize a Pet with a name, species, and optional age."""
        self.name = name
        self.species = species.lower()
        self.age = age
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove a task by description. Returns True if found and removed."""
        for i, t in enumerate(self.tasks):
            if t.description == description:
                self.tasks.pop(i)
                return True
        return False

    def pending_tasks(self) -> list[Task]:
        """Return tasks that have not yet been marked complete."""
        return [t for t in self.tasks if not t.completed]

    def completed_tasks(self) -> list[Task]:
        """Return tasks that have been marked complete today."""
        return [t for t in self.tasks if t.completed]

    def __repr__(self) -> str:
        """Return a concise string representation of the pet for debugging."""
        return f"Pet(name={self.name!r}, species={self.species!r}, tasks={len(self.tasks)})"


# ─────────────────────────────────────────────
# Owner
# ─────────────────────────────────────────────

class Owner:
    """
    Manages multiple pets and provides a unified view of all their tasks.

    Attributes
    ----------
    name    : str
    contact : str   optional phone / email
    pets    : list[Pet]
    """

    def __init__(self, name: str, contact: str = ""):
        """Initialize an Owner with a name and optional contact info."""
        self.name = name
        self.contact = contact
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove a pet by name. Returns True if found and removed."""
        for i, p in enumerate(self.pets):
            if p.name == name:
                self.pets.pop(i)
                return True
        return False

    def get_pet(self, name: str) -> Optional[Pet]:
        """Look up a pet by name."""
        for p in self.pets:
            if p.name == name:
                return p
        return None

    def all_tasks(self) -> list[tuple]:
        """
        Return every task across all pets as (Pet, Task) pairs.
        This is the main entry point the Scheduler uses to retrieve tasks.
        """
        result = []
        for pet in self.pets:
            for task in pet.tasks:
                result.append((pet, task))
        return result

    def all_pending_tasks(self) -> list[tuple]:
        """Return (Pet, Task) pairs for every incomplete task across all pets."""
        return [(pet, task) for pet, task in self.all_tasks() if not task.completed]

    def all_completed_tasks(self) -> list[tuple]:
        """Return (Pet, Task) pairs for every completed task across all pets."""
        return [(pet, task) for pet, task in self.all_tasks() if task.completed]

    def __repr__(self) -> str:
        """Return a concise string representation of the owner for debugging."""
        return f"Owner(name={self.name!r}, pets={len(self.pets)})"


# ─────────────────────────────────────────────
# Scheduler
# ─────────────────────────────────────────────

class Scheduler:
    """
    The 'brain' of PawPal+.

    Receives an Owner and orchestrates all pet tasks:
    - retrieves tasks via owner.all_tasks()        (Owner → Pet → Task)
    - sorts and filters by priority
    - marks tasks complete
    - produces a daily plan and summary report

    The Scheduler does NOT store tasks itself — it always reads
    live data through the Owner hierarchy.
    """

    def __init__(self, owner: Owner):
        """Initialize the Scheduler with an Owner whose pets and tasks it will manage."""
        self.owner = owner

    # ── Task retrieval ────────────────────────

    def get_schedule(self) -> list[tuple]:
        """
        Return every task across all pets as a sorted list of (Pet, Task) pairs.

        Sort order (applied left-to-right as a tuple key):
          1. Completion status — incomplete tasks (False) sort before done (True).
          2. Scheduled time    — earliest "HH:MM" first; "anytime" sorts last.
          3. Priority          — highest numeric priority breaks ties at the same time.

        Returns
        -------
        list[tuple[Pet, Task]]
            All tasks, pending first, then chronological within each group.
        """
        return sorted(
            self.owner.all_tasks(),
            key=lambda pt: (
                pt[1].completed,
                _parse_time(pt[1].time),
                -pt[1].priority_value(),
            ),
        )

    def get_pending_tasks(self) -> list[tuple]:
        """
        Return only incomplete tasks, sorted by time then priority.

        Delegates to get_schedule() for ordering and filters out any task
        whose completed flag is True.

        Returns
        -------
        list[tuple[Pet, Task]]
            Incomplete (Pet, Task) pairs in chronological, priority order.
        """
        return [
            (pet, task)
            for pet, task in self.get_schedule()
            if not task.completed
        ]

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """
        Return all tasks belonging to a single named pet, sorted by time then priority.

        Parameters
        ----------
        pet_name : str
            Exact name of the pet (case-sensitive; use Owner.get_pet for lookup).

        Returns
        -------
        list[Task]
            Sorted tasks for the pet, or an empty list if the pet is not found.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return []
        return sorted(pet.tasks, key=lambda t: (_parse_time(t.time), -t.priority_value()))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """
        Sort a list of Task objects chronologically by their 'time' attribute.

        How the lambda key works
        ------------------------
        Python's sorted() accepts a 'key' argument — a callable that receives
        each element and returns a value used for comparison.

        Here the lambda receives a single Task (t) and returns a datetime object
        produced by _parse_time(t.time):

            key=lambda t: _parse_time(t.time)
                  ^               ^
                  |               └─ converts "HH:MM" string → datetime
                  └─ each Task passed in one at a time

        sorted() then orders Tasks from earliest datetime to latest.
        Tasks with no valid "HH:MM" time (e.g. "anytime") get datetime.max
        so they sort to the end of the list.

        Examples
        --------
        Input times : ["14:00", "anytime", "07:30", "09:00"]
        Sorted order: ["07:30", "09:00", "14:00", "anytime"]
        """
        return sorted(tasks, key=lambda t: _parse_time(t.time))

    def filter_by_status(self, status: str) -> list[tuple]:
        """
        Filter all tasks by completion status.

        Parameters
        ----------
        status : str
            "pending"   — return only incomplete tasks
            "completed" — return only finished tasks
            any other value returns all tasks unchanged

        Returns
        -------
        list of (Pet, Task) pairs matching the requested status,
        sorted chronologically by task time.

        How it works
        ------------
        A list comprehension walks every (Pet, Task) pair from the owner
        and keeps only those where t.completed matches the requested status:

            [(p, t) for p, t in all_tasks if not t.completed]
             ^                               ^
             keep the pair                  the filter condition

        The result is then passed through sort_by_time() so the caller
        always receives tasks in chronological order.

        Examples
        --------
        >>> scheduler.filter_by_status("pending")
        [(Pet('Luna'), Task('Feed', '07:00')), ...]

        >>> scheduler.filter_by_status("completed")
        [(Pet('Rex'), Task('Walk', '08:00')), ...]
        """
        all_tasks = self.owner.all_tasks()

        if status == "pending":
            filtered = [(p, t) for p, t in all_tasks if not t.completed]
        elif status == "completed":
            filtered = [(p, t) for p, t in all_tasks if t.completed]
        else:
            filtered = all_tasks

        # Return in chronological order
        return sorted(filtered, key=lambda pt: _parse_time(pt[1].time))

    def filter_by_pet(self, pet_name: str) -> list[tuple]:
        """
        Filter all tasks to only those belonging to a specific pet.

        Parameters
        ----------
        pet_name : str
            The pet's name. Comparison is case-insensitive so "mochi"
            matches a pet named "Mochi".

        Returns
        -------
        list of (Pet, Task) pairs for the named pet, sorted chronologically.
        Returns an empty list if no pet with that name exists.

        How it works
        ------------
        The comprehension checks each pair's Pet object by lowercasing both
        sides of the comparison so capitalization never causes a mismatch:

            p.name.lower() == pet_name.lower()

        Examples
        --------
        >>> scheduler.filter_by_pet("Luna")
        [(Pet('Luna'), Task('Feed', '07:00')), (Pet('Luna'), Task('Pills', '09:00'))]

        >>> scheduler.filter_by_pet("unknown")   # pet doesn't exist
        []
        """
        filtered = [
            (p, t)
            for p, t in self.owner.all_tasks()
            if p.name.lower() == pet_name.lower()
        ]
        return sorted(filtered, key=lambda pt: _parse_time(pt[1].time))

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,
        time_after: Optional[str] = None,
        time_before: Optional[str] = None,
    ) -> list[tuple]:
        """
        Combine any mix of filters in a single call. All parameters are optional;
        omitting one means that axis is not filtered.

          pet_name   — case-insensitive pet name match
          status     — "pending" or "completed"
          time_after — "HH:MM" lower bound (inclusive)
          time_before— "HH:MM" upper bound (inclusive)

        Internally delegates to filter_by_pet / filter_by_status so the
        individual methods remain the single source of truth.
        """
        results = self.owner.all_tasks()

        if pet_name:
            results = [(p, t) for p, t in results if p.name.lower() == pet_name.lower()]
        if status == "pending":
            results = [(p, t) for p, t in results if not t.completed]
        elif status == "completed":
            results = [(p, t) for p, t in results if t.completed]
        if time_after:
            cutoff = _parse_time(time_after)
            results = [(p, t) for p, t in results if _parse_time(t.time) >= cutoff]
        if time_before:
            cutoff = _parse_time(time_before)
            results = [(p, t) for p, t in results if _parse_time(t.time) <= cutoff]

        return sorted(results, key=lambda pt: _parse_time(pt[1].time))

    def next_due(self, task: "Task") -> Optional[date]:
        """Return the date this task is next due based on its frequency."""
        today = date.today()
        if not task.completed:
            return today
        offsets = {"daily": 1, "twice daily": 1, "weekly": 7}
        delta = offsets.get(task.frequency)
        return today + timedelta(days=delta) if delta else None

    def detect_conflicts(self) -> list[dict]:
        """
        Lightweight conflict detection — never raises, always returns a list.

        Checks two kinds of overlap, both keyed on (due_date, time) so
        next-occurrence copies on future dates are never flagged against
        today's completed instance:

        1. Same-pet conflict  — two tasks for one pet at the same slot.
        2. Cross-pet conflict — tasks for different pets at the same slot
                                (owner cannot be in two places at once).

        Returns a list of conflict dicts, each with:
            scope    : "same-pet" | "cross-pet"
            pets     : list of pet names involved
            due_date : date the conflict occurs
            time     : "HH:MM" time slot
            tasks    : list of task descriptions that collide
        """
        conflicts: list[dict] = []

        # ── 1. Same-pet conflicts ─────────────────────────────────────────
        for pet in self.owner.pets:
            by_slot: dict[tuple, list] = {}
            for task in pet.tasks:
                if task.time and task.time != "anytime":
                    slot = (task.due_date, task.time)
                    by_slot.setdefault(slot, []).append(task)
            for (due, time_slot), tasks in by_slot.items():
                if len(tasks) > 1:
                    conflicts.append({
                        "scope":    "same-pet",
                        "pets":     [pet.name],
                        "due_date": due,
                        "time":     time_slot,
                        "tasks":    [t.description for t in tasks],
                    })

        # ── 2. Cross-pet conflicts ────────────────────────────────────────
        # Build a flat index: (due_date, time) → [(pet_name, task_description)]
        cross_index: dict[tuple, list] = {}
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.time and task.time != "anytime":
                    slot = (task.due_date, task.time)
                    cross_index.setdefault(slot, []).append((pet.name, task.description))

        for (due, time_slot), entries in cross_index.items():
            pet_names = [e[0] for e in entries]
            # A cross-pet conflict requires at least two *different* pets
            if len(set(pet_names)) > 1:
                conflicts.append({
                    "scope":    "cross-pet",
                    "pets":     sorted(set(pet_names)),
                    "due_date": due,
                    "time":     time_slot,
                    "tasks":    [f"{p}: {t}" for p, t in entries],
                })

        return conflicts

    def conflict_warnings(self) -> list[str]:
        """
        Return human-readable warning strings for every detected conflict.

        Designed to be lightweight and safe — returns an empty list when
        there are no conflicts, never raises an exception.

        Same-pet warning format:
            WARNING [same-pet] Luna on 2026-03-30 @ 07:00 — 'Task A' vs 'Task B'

        Cross-pet warning format:
            WARNING [cross-pet] Luna & Rex on 2026-03-30 @ 08:00
              Luna: Morning pills | Rex: Morning walk

        Usage
        -----
        for msg in scheduler.conflict_warnings():
            print(msg)
        """
        warnings: list[str] = []
        for c in self.detect_conflicts():
            if c["scope"] == "same-pet":
                task_str = " vs ".join(f"'{t}'" for t in c["tasks"])
                warnings.append(
                    f"WARNING [same-pet]  {c['pets'][0]} "
                    f"on {c['due_date']} @ {c['time']} — {task_str}"
                )
            else:
                pets_str = " & ".join(c["pets"])
                tasks_str = " | ".join(c["tasks"])
                warnings.append(
                    f"WARNING [cross-pet] {pets_str} "
                    f"on {c['due_date']} @ {c['time']}\n"
                    f"          {tasks_str}"
                )
        return warnings

    # ── Actions ───────────────────────────────

    def add_task(self, pet_name: str, task: Task) -> bool:
        """Add a task to a named pet. Returns True if the pet was found."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        pet.add_task(task)
        return True

    def remove_task(self, pet_name: str, description: str) -> bool:
        """Remove a task from a named pet by description."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        return pet.remove_task(description)

    def complete_task(self, pet_name: str, description: str) -> bool:
        """
        Mark a specific task done for a named pet.

        For recurring tasks ("daily", "twice daily", "weekly") a new Task
        instance is automatically created for the next occurrence using
        timedelta and added to the pet's task list.

        Returns True if the task was found and marked.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        for task in pet.tasks:
            if task.description == description and not task.completed:
                task.mark_complete()
                # Auto-schedule the next occurrence for recurring tasks.
                # task.next_occurrence() returns None for "once"/"as needed",
                # so we only add a new task when a future date exists.
                next_task = task.next_occurrence()
                if next_task is not None:
                    pet.add_task(next_task)
                return True
        return False

    def reset_daily_tasks(self) -> None:
        """
        Reset recurring tasks for a new day.
        One-time tasks ('once', 'as needed') keep their completed status.
        """
        recurring = {"daily", "twice daily", "weekly"}
        for _, task in self.owner.all_tasks():
            if task.frequency in recurring:
                task.reset()

    def reset_all_tasks(self) -> None:
        """Clear completion status on every task regardless of frequency."""
        for _, task in self.owner.all_tasks():
            task.reset()

    # ── Reporting ─────────────────────────────

    def daily_plan(self) -> list[dict]:
        """
        Return the day's pending tasks as display-ready dicts,
        each including the pet's name alongside the task fields.
        """
        plan = []
        for pet, task in self.get_pending_tasks():
            row = {"pet": pet.name, "species": pet.species}
            row.update(task.to_dict())
            plan.append(row)
        return plan

    def summary(self) -> str:
        """Human-readable daily summary across all pets."""
        all_tasks = self.owner.all_tasks()
        total = len(all_tasks)
        done = sum(1 for _, t in all_tasks if t.completed)
        pending = total - done

        lines = [
            f"=== PawPal+ Daily Summary for {self.owner.name} ===",
            f"Pets   : {', '.join(p.name for p in self.owner.pets) or 'none'}",
            f"Tasks  : {done}/{total} complete, {pending} pending",
        ]

        for pet in self.owner.pets:
            lines.append(f"\n  {pet.name} ({pet.species})")
            if not pet.tasks:
                lines.append("    No tasks assigned.")
                continue
            for task in sorted(pet.tasks, key=lambda t: -t.priority_value()):
                status = (
                    f"done at {task.completed_at.strftime('%H:%M')}"
                    if task.completed
                    else "pending"
                )
                lines.append(
                    f"    [{task.priority.upper()}] {task.description} "
                    f"@ {task.time} ({task.frequency}) — {status}"
                )

        return "\n".join(lines)
