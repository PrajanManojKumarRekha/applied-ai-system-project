from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Task:
    description: str
    time: str
    frequency: str
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

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks from every pet owned by the owner."""
        return self.owner.get_all_tasks()

    def get_todays_schedule(self) -> List[Task]:
        """Return all tasks sorted by time for today."""
        return sorted(self.get_all_tasks(), key=self._time_key)

    def get_pending_schedule(self) -> List[Task]:
        """Return only incomplete tasks sorted by time."""
        pending = self.owner.get_all_pending_tasks()
        return sorted(pending, key=self._time_key)
