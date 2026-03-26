from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, List, Optional


@dataclass
class Task:
    description: str
    time: str
    frequency: str
    duration_minutes: int = 30
    priority: str = "medium"
    due_date: date = field(default_factory=date.today)
    completed: bool = False

    def __post_init__(self) -> None:
        """Validate task values to keep scheduler input safe and consistent."""
        self.description = self.description.strip()
        self.frequency = self.frequency.strip().lower()
        self.priority = self.priority.strip().lower()

        if not self.description:
            raise ValueError("Task description cannot be empty.")

        try:
            datetime.strptime(self.time, "%H:%M")
        except ValueError as exc:
            raise ValueError("Task time must be in HH:MM format.") from exc

        if self.frequency not in {"daily", "weekly", "as needed"}:
            raise ValueError("Task frequency must be daily, weekly, or as needed.")

        if self.priority not in {"high", "medium", "low"}:
            raise ValueError("Task priority must be high, medium, or low.")

        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be greater than zero.")

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark the task as not completed."""
        self.completed = False


@dataclass
class Pet:
    name: str
    species: str
    care_notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def update_notes(self, notes: str) -> None:
        """Update the pet care notes."""
        self.care_notes = notes

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        if not isinstance(task, Task):
            raise TypeError("Pet.add_task expects a Task instance.")
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        return self.tasks

    def get_pending_tasks(self) -> List[Task]:
        """Return incomplete tasks for this pet."""
        return [task for task in self.tasks if not task.completed]


@dataclass
class Owner:
    name: str
    daily_time_available: int = 180
    preferred_task_types: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize owner inputs and validate available time."""
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Owner name cannot be empty.")
        if self.daily_time_available <= 0:
            raise ValueError("Owner daily time must be greater than zero.")
        self.preferred_task_types = [item.strip().lower() for item in self.preferred_task_types if item.strip()]

    def add_pet(self, pet: Pet) -> None:
        """Add a pet for this owner."""
        if self.get_pet_by_name(pet.name) is not None:
            raise ValueError(f"Pet named '{pet.name}' already exists.")
        self.pets.append(pet)

    def set_daily_time_available(self, minutes: int) -> None:
        """Set the daily minutes available for scheduling."""
        if minutes <= 0:
            raise ValueError("Daily time must be greater than zero.")
        self.daily_time_available = minutes

    def set_preferences(self, preferred_task_types: List[str]) -> None:
        """Set owner task preferences used by planning logic."""
        self.preferred_task_types = [item.strip().lower() for item in preferred_task_types if item.strip()]

    def get_pet_by_name(self, pet_name: str) -> Optional[Pet]:
        """Return the pet with this name or None if it is missing."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> List[Task]:
        """Return tasks from all pets."""
        all_tasks: List[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def get_all_pending_tasks(self) -> List[Task]:
        """Return incomplete tasks from all pets."""
        pending_tasks: List[Task] = []
        for pet in self.pets:
            pending_tasks.extend(pet.get_pending_tasks())
        return pending_tasks


@dataclass
class Scheduler:
    owner: Owner

    PRIORITY_SCORES = {"high": 3, "medium": 2, "low": 1}

    def _time_key(self, task: Task) -> datetime:
        """Convert task time text into a sortable datetime value."""
        return datetime.strptime(task.time, "%H:%M")

    def _next_due_date(self, task: Task) -> Optional[date]:
        """Return the next due date for recurring tasks, or None otherwise."""
        frequency = task.frequency.strip().lower()
        if frequency == "daily":
            return task.due_date + timedelta(days=1)
        if frequency == "weekly":
            return task.due_date + timedelta(weeks=1)
        return None

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks from every pet owned by the owner."""
        return self.owner.get_all_tasks()

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Return tasks sorted by time in HH:MM format."""
        return sorted(tasks, key=self._time_key)

    def sort_by_priority_then_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority first, then by time."""
        return sorted(
            tasks,
            key=lambda task: (-self.PRIORITY_SCORES.get(task.priority, 0), self._time_key(task)),
        )

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[tuple[str, Task]]:
        """Return tasks filtered by pet name and or completion status."""
        filtered: List[tuple[str, Task]] = []
        for pet in self.owner.pets:
            if pet_name and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                filtered.append((pet.name, task))

        return sorted(filtered, key=lambda pair: self._time_key(pair[1]))

    def get_todays_schedule(self) -> List[Task]:
        """Return all tasks sorted by time for today."""
        today_tasks = [task for task in self.get_all_tasks() if task.due_date == date.today()]
        return self.sort_by_time(today_tasks)

    def get_pending_schedule(self) -> List[Task]:
        """Return only incomplete tasks sorted by time."""
        pending = [task for task in self.owner.get_all_pending_tasks() if task.due_date == date.today()]
        return self.sort_by_time(pending)

    def build_daily_plan(
        self,
        daily_minutes_available: Optional[int] = None,
        pet_name: Optional[str] = None,
    ) -> List[dict[str, Any]]:
        """Build an explainable daily plan based on time and priority constraints."""
        minutes_budget = (
            self.owner.daily_time_available if daily_minutes_available is None else daily_minutes_available
        )
        if minutes_budget <= 0:
            raise ValueError("Daily minutes available must be greater than zero.")

        pending_today = [task for task in self.owner.get_all_pending_tasks() if task.due_date == date.today()]
        if pet_name:
            target_pet = self.owner.get_pet_by_name(pet_name)
            if target_pet is None:
                return []
            pending_today = [task for task in target_pet.get_pending_tasks() if task.due_date == date.today()]

        ranked_tasks = self.sort_by_priority_then_time(pending_today)

        plan: List[dict[str, Any]] = []
        used_minutes = 0
        for task in ranked_tasks:
            if used_minutes + task.duration_minutes > minutes_budget:
                continue

            reason = (
                f"Selected {task.description} at {task.time} because it is {task.priority} priority "
                f"and fits the remaining {minutes_budget - used_minutes} minutes."
            )
            plan.append(
                {
                    "time": task.time,
                    "description": task.description,
                    "priority": task.priority,
                    "duration_minutes": task.duration_minutes,
                    "due_date": task.due_date.isoformat(),
                    "reason": reason,
                }
            )
            used_minutes += task.duration_minutes

        return sorted(plan, key=lambda item: datetime.strptime(item["time"], "%H:%M"))

    def explain_plan(self, plan: List[dict[str, Any]]) -> List[str]:
        """Return plain language reasons for each task in a built plan."""
        return [item["reason"] for item in plan]

    def mark_task_complete(self, pet_name: str, task_description: str, task_time: str) -> bool:
        """Mark one matching task complete and create next recurring task if needed."""
        pet = self.owner.get_pet_by_name(pet_name)
        if pet is None:
            return False

        for task in pet.tasks:
            if task.description == task_description and task.time == task_time and not task.completed:
                task.mark_complete()

                next_due = self._next_due_date(task)
                if next_due is not None:
                    pet.add_task(
                        Task(
                            description=task.description,
                            time=task.time,
                            frequency=task.frequency,
                            duration_minutes=task.duration_minutes,
                            priority=task.priority,
                            due_date=next_due,
                        )
                    )
                return True

        return False

    def detect_conflicts(self) -> List[str]:
        """Return warning messages when two or more pending tasks share the same due date and time."""
        slots: dict[tuple[date, str], List[tuple[str, str]]] = {}
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.completed:
                    continue
                key = (task.due_date, task.time)
                slots.setdefault(key, []).append((pet.name, task.description))

        warnings: List[str] = []
        for (due_date, time_text), task_refs in slots.items():
            if len(task_refs) < 2:
                continue
            details = ", ".join(f"{pet_name}: {desc}" for pet_name, desc in task_refs)
            warnings.append(f"Conflict at {time_text} on {due_date.isoformat()}: {details}")

        return warnings
