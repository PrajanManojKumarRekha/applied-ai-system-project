from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    title: str
    category: str
    duration_minutes: int
    priority: str
    required: bool = False
    completed: bool = False

    def mark_done(self) -> None:
        """Mark this task as completed."""
        raise NotImplementedError

    def fits_in(self, remaining_minutes: int) -> bool:
        """Return True if task can fit in remaining time."""
        raise NotImplementedError


@dataclass
class Pet:
    name: str
    species: str
    care_notes: str = ""

    def update_notes(self, notes: str) -> None:
        """Update pet care notes."""
        raise NotImplementedError


@dataclass
class Owner:
    name: str
    daily_time_available: int
    preferred_task_types: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet for this owner."""
        raise NotImplementedError

    def add_task(self, task: Task) -> None:
        """Add a care task for this owner."""
        raise NotImplementedError

    def set_time_limit(self, minutes: int) -> None:
        """Set total minutes available for the day."""
        raise NotImplementedError


@dataclass
class PlanItem:
    task: Task
    start_time: str
    end_time: str
    reason: str


@dataclass
class Scheduler:
    time_limit_minutes: int

    def score_task(self, task: Task, owner: Optional[Owner] = None) -> int:
        """Return a score for ranking tasks."""
        raise NotImplementedError

    def build_plan(self, owner: Owner) -> List[PlanItem]:
        """Build a day plan from owner tasks and constraints."""
        raise NotImplementedError

    def explain_plan(self, plan: List[PlanItem]) -> List[str]:
        """Return plain language reasons for the plan."""
        raise NotImplementedError
