from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional


@dataclass
class Task:
    description: str
    time: str
    frequency: str
    due_date: date = field(default_factory=date.today)
    completed: bool = False

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
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet for this owner."""
        self.pets.append(pet)

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
