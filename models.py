"""
PawPal+ core domain classes.

Classes
-------
Owner     -- person responsible for the pet
Pet       -- the animal being cared for
Task      -- a single care activity (walk, meal, drink, etc.)
Scheduler -- manages tasks for a pet and tracks completions
"""

from datetime import datetime
from typing import Optional


class Owner:
    """Represents the pet owner."""

    def __init__(self, name: str, contact: str = ""):
        self.name = name
        self.contact = contact

    def __repr__(self) -> str:
        return f"Owner(name={self.name!r})"


class Pet:
    """Represents the pet being cared for."""

    KNOWN_SPECIES = {"cat", "dog", "bird", "rabbit", "other"}

    def __init__(self, name: str, species: str, owner: Owner):
        self.name = name
        self.species = species.lower()
        self.owner = owner

    def __repr__(self) -> str:
        return f"Pet(name={self.name!r}, species={self.species!r}, owner={self.owner.name!r})"


class Task:
    """A single pet-care activity."""

    CATEGORIES = {"walk", "eat", "drink", "medication", "play", "grooming", "other"}
    PRIORITIES = {"low": 1, "medium": 2, "high": 3}

    def __init__(
        self,
        title: str,
        category: str,
        duration_minutes: int,
        priority: str = "medium",
        notes: str = "",
    ):
        if category not in self.CATEGORIES:
            category = "other"
        if priority not in self.PRIORITIES:
            priority = "medium"

        self.title = title
        self.category = category
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.notes = notes
        self.completed: bool = False
        self.completed_at: Optional[datetime] = None

    def mark_complete(self) -> None:
        self.completed = True
        self.completed_at = datetime.now()

    def priority_value(self) -> int:
        return self.PRIORITIES[self.priority]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "category": self.category,
            "duration (min)": self.duration_minutes,
            "priority": self.priority,
            "completed": "Yes" if self.completed else "No",
            "completed at": self.completed_at.strftime("%H:%M") if self.completed_at else "—",
        }

    def __repr__(self) -> str:
        status = "done" if self.completed else "pending"
        return f"Task({self.title!r}, {self.category}, {self.priority}, {status})"


class Scheduler:
    """
    Manages daily care tasks for a pet.

    Responsibilities
    ----------------
    - Store tasks and sort them by priority
    - Mark individual tasks complete
    - Report what's done and what's still pending
    """

    def __init__(self, pet: Pet):
        self.pet = pet
        self._tasks: list[Task] = []

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Add a task to the schedule."""
        self._tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove a task by title. Returns True if found and removed."""
        for i, t in enumerate(self._tasks):
            if t.title == title:
                self._tasks.pop(i)
                return True
        return False

    def complete_task(self, title: str) -> bool:
        """Mark a task complete by title. Returns True if found."""
        for t in self._tasks:
            if t.title == title and not t.completed:
                t.mark_complete()
                return True
        return False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_schedule(self) -> list[Task]:
        """Return all tasks sorted high → low priority, pending first."""
        return sorted(
            self._tasks,
            key=lambda t: (t.completed, -t.priority_value()),
        )

    def pending_tasks(self) -> list[Task]:
        return [t for t in self._tasks if not t.completed]

    def completed_tasks(self) -> list[Task]:
        return [t for t in self._tasks if t.completed]

    def summary(self) -> str:
        """Human-readable daily summary."""
        total = len(self._tasks)
        done = len(self.completed_tasks())
        pending = total - done
        lines = [
            f"--- Daily Care Plan for {self.pet.name} ({self.pet.species}) ---",
            f"Owner : {self.pet.owner.name}",
            f"Tasks : {done}/{total} complete, {pending} pending",
        ]
        if self.pending_tasks():
            lines.append("\nStill to do:")
            for t in sorted(self.pending_tasks(), key=lambda x: -x.priority_value()):
                lines.append(f"  [{t.priority.upper()}] {t.title} ({t.duration_minutes} min)")
        if self.completed_tasks():
            lines.append("\nCompleted:")
            for t in self.completed_tasks():
                lines.append(f"  ✓ {t.title} at {t.completed_at.strftime('%H:%M')}")
        return "\n".join(lines)
