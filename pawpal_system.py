import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
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
        self.completed = True

    def mark_incomplete(self) -> None:
        self.completed = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "time": self.time,
            "frequency": self.frequency,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "due_date": self.due_date.isoformat(),
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Task":
        return cls(
            description=payload["description"],
            time=payload["time"],
            frequency=payload["frequency"],
            duration_minutes=int(payload.get("duration_minutes", 30)),
            priority=payload.get("priority", "medium"),
            due_date=date.fromisoformat(payload.get("due_date", date.today().isoformat())),
            completed=bool(payload.get("completed", False)),
        )


@dataclass
class HealthRecord:
    record_type: str
    description: str
    record_date: date = field(default_factory=date.today)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_type": self.record_type,
            "description": self.description,
            "record_date": self.record_date.isoformat(),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HealthRecord":
        return cls(
            record_type=payload.get("record_type", "general"),
            description=payload["description"],
            record_date=date.fromisoformat(payload.get("record_date", date.today().isoformat())),
            notes=payload.get("notes", ""),
        )


@dataclass
class Pet:
    name: str
    species: str
    care_notes: str = ""
    tasks: List[Task] = field(default_factory=list)
    health_records: List[HealthRecord] = field(default_factory=list)
    streak_days: int = 0
    last_streak_date: Optional[date] = None

    def update_notes(self, notes: str) -> None:
        self.care_notes = notes

    def add_task(self, task: Task) -> None:
        if not isinstance(task, Task):
            raise TypeError("Pet.add_task expects a Task instance.")
        self.tasks.append(task)

    def add_health_record(self, record: HealthRecord) -> None:
        if not isinstance(record, HealthRecord):
            raise TypeError("Pet.add_health_record expects a HealthRecord instance.")
        self.health_records.append(record)

    def get_tasks(self) -> List[Task]:
        return self.tasks

    def get_pending_tasks(self) -> List[Task]:
        return [task for task in self.tasks if not task.completed]

    def get_health_records(self) -> List[HealthRecord]:
        return sorted(self.health_records, key=lambda r: r.record_date, reverse=True)

    def update_streak(self) -> None:
        """Recalculate consecutive-day completion streak for daily tasks."""
        today = date.today()
        daily_tasks_today = [
            t for t in self.tasks
            if t.frequency == "daily" and t.due_date == today
        ]
        if not daily_tasks_today:
            return

        all_done = all(t.completed for t in daily_tasks_today)
        if all_done:
            if self.last_streak_date == today - timedelta(days=1) or self.last_streak_date == today:
                if self.last_streak_date != today:
                    self.streak_days += 1
                    self.last_streak_date = today
            else:
                self.streak_days = 1
                self.last_streak_date = today
        else:
            if self.last_streak_date != today:
                self.streak_days = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "species": self.species,
            "care_notes": self.care_notes,
            "tasks": [task.to_dict() for task in self.tasks],
            "health_records": [r.to_dict() for r in self.health_records],
            "streak_days": self.streak_days,
            "last_streak_date": self.last_streak_date.isoformat() if self.last_streak_date else None,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Pet":
        last_streak_raw = payload.get("last_streak_date")
        return cls(
            name=payload["name"],
            species=payload["species"],
            care_notes=payload.get("care_notes", ""),
            tasks=[Task.from_dict(item) for item in payload.get("tasks", [])],
            health_records=[HealthRecord.from_dict(r) for r in payload.get("health_records", [])],
            streak_days=int(payload.get("streak_days", 0)),
            last_streak_date=date.fromisoformat(last_streak_raw) if last_streak_raw else None,
        )


@dataclass
class Owner:
    name: str
    daily_time_available: int = 180
    preferred_task_types: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Owner name cannot be empty.")
        if self.daily_time_available <= 0:
            raise ValueError("Owner daily time must be greater than zero.")
        self.preferred_task_types = [item.strip().lower() for item in self.preferred_task_types if item.strip()]

    def add_pet(self, pet: Pet) -> None:
        if self.get_pet_by_name(pet.name) is not None:
            raise ValueError(f"Pet named '{pet.name}' already exists.")
        self.pets.append(pet)

    def set_daily_time_available(self, minutes: int) -> None:
        if minutes <= 0:
            raise ValueError("Daily time must be greater than zero.")
        self.daily_time_available = minutes

    def set_preferences(self, preferred_task_types: List[str]) -> None:
        self.preferred_task_types = [item.strip().lower() for item in preferred_task_types if item.strip()]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "daily_time_available": self.daily_time_available,
            "preferred_task_types": self.preferred_task_types,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    def save_to_json(self, file_path: str = "data.json") -> None:
        path = Path(file_path)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Owner":
        return cls(
            name=payload.get("name", "Jordan"),
            daily_time_available=int(payload.get("daily_time_available", 180)),
            preferred_task_types=payload.get("preferred_task_types", []),
            pets=[Pet.from_dict(item) for item in payload.get("pets", [])],
        )

    @classmethod
    def load_from_json(cls, file_path: str = "data.json") -> "Owner":
        path = Path(file_path)
        if not path.exists():
            return cls(name="Jordan")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(payload)

    @staticmethod
    def load_all(file_path: str = "owners.json") -> "list[Owner]":
        """Load all owners. Falls back to legacy data.json on first run."""
        path = Path(file_path)
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            return [Owner.from_dict(o) for o in raw]
        legacy = Path("data.json")
        if legacy.exists():
            try:
                owner = Owner.from_dict(json.loads(legacy.read_text(encoding="utf-8")))
                Owner.save_all([owner], file_path)
                return [owner]
            except Exception:
                pass
        default = Owner(name="My Account")
        Owner.save_all([default], file_path)
        return [default]

    @staticmethod
    def save_all(owners: "list[Owner]", file_path: str = "owners.json") -> None:
        path = Path(file_path)
        path.write_text(json.dumps([o.to_dict() for o in owners], indent=2), encoding="utf-8")

    def get_pet_by_name(self, pet_name: str) -> Optional[Pet]:
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> List[Task]:
        all_tasks: List[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def get_all_pending_tasks(self) -> List[Task]:
        pending_tasks: List[Task] = []
        for pet in self.pets:
            pending_tasks.extend(pet.get_pending_tasks())
        return pending_tasks

    def completion_rate(self) -> float:
        all_tasks = self.get_all_tasks()
        if not all_tasks:
            return 0.0
        done = sum(1 for t in all_tasks if t.completed)
        return round(done / len(all_tasks), 2)

    def total_minutes_scheduled(self) -> int:
        return sum(t.duration_minutes for t in self.get_all_tasks())

    def total_minutes_completed(self) -> int:
        return sum(t.duration_minutes for t in self.get_all_tasks() if t.completed)


@dataclass
class Scheduler:
    owner: Owner

    PRIORITY_SCORES = {"high": 3, "medium": 2, "low": 1}

    def _time_key(self, task: Task) -> datetime:
        return datetime.strptime(task.time, "%H:%M")

    def _next_due_date(self, task: Task) -> Optional[date]:
        frequency = task.frequency.strip().lower()
        if frequency == "daily":
            return task.due_date + timedelta(days=1)
        if frequency == "weekly":
            return task.due_date + timedelta(weeks=1)
        return None

    def get_all_tasks(self) -> List[Task]:
        return self.owner.get_all_tasks()

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        return sorted(tasks, key=self._time_key)

    def sort_by_priority_then_time(self, tasks: List[Task]) -> List[Task]:
        return sorted(
            tasks,
            key=lambda task: (-self.PRIORITY_SCORES.get(task.priority, 0), self._time_key(task)),
        )

    def score_task(self, task: Task) -> int:
        score = self.PRIORITY_SCORES.get(task.priority, 0) * 10
        description_lower = task.description.lower()
        if any(keyword in description_lower for keyword in self.owner.preferred_task_types):
            score += 5
        if task.frequency == "daily":
            score += 2
        return score

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[tuple[str, Task]]:
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
        today_tasks = [task for task in self.get_all_tasks() if task.due_date == date.today()]
        return self.sort_by_time(today_tasks)

    def get_pending_schedule(self) -> List[Task]:
        pending = [task for task in self.owner.get_all_pending_tasks() if task.due_date == date.today()]
        return self.sort_by_time(pending)

    def build_daily_plan(
        self,
        daily_minutes_available: Optional[int] = None,
        pet_name: Optional[str] = None,
    ) -> List[dict[str, Any]]:
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

        ranked_tasks = sorted(
            pending_today,
            key=lambda task: (-self.score_task(task), self._time_key(task)),
        )

        plan: List[dict[str, Any]] = []
        used_minutes = 0
        for task in ranked_tasks:
            if used_minutes + task.duration_minutes > minutes_budget:
                continue

            reason = (
                f"Selected {task.description} at {task.time} because it is {task.priority} priority "
                "and fits the daily time budget."
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
        return [item["reason"] for item in plan]

    def mark_task_complete(self, pet_name: str, task_description: str, task_time: str) -> bool:
        pet = self.owner.get_pet_by_name(pet_name)
        if pet is None:
            return False

        for task in pet.tasks:
            if task.description == task_description and task.time == task_time and not task.completed:
                task.mark_complete()
                pet.update_streak()

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

    def next_available_slot(
        self,
        duration_minutes: int,
        target_date: Optional[date] = None,
        start_time: str = "06:00",
        end_time: str = "22:00",
        pet_name: Optional[str] = None,
    ) -> Optional[str]:
        if duration_minutes <= 0:
            raise ValueError("Duration must be greater than zero.")

        schedule_date = date.today() if target_date is None else target_date
        start_dt = datetime.combine(schedule_date, datetime.strptime(start_time, "%H:%M").time())
        end_dt = datetime.combine(schedule_date, datetime.strptime(end_time, "%H:%M").time())
        if end_dt <= start_dt:
            raise ValueError("End time must be after start time.")

        tasks_for_day: List[Task] = []
        if pet_name:
            pet = self.owner.get_pet_by_name(pet_name)
            if pet is None:
                return None
            tasks_for_day = [task for task in pet.get_pending_tasks() if task.due_date == schedule_date]
        else:
            tasks_for_day = [task for task in self.owner.get_all_pending_tasks() if task.due_date == schedule_date]

        tasks_sorted = self.sort_by_time(tasks_for_day)
        cursor = start_dt
        for task in tasks_sorted:
            task_start = datetime.combine(schedule_date, datetime.strptime(task.time, "%H:%M").time())
            if task_start - cursor >= timedelta(minutes=duration_minutes):
                return cursor.strftime("%H:%M")

            task_end = task_start + timedelta(minutes=task.duration_minutes)
            if task_end > cursor:
                cursor = task_end

        if end_dt - cursor >= timedelta(minutes=duration_minutes):
            return cursor.strftime("%H:%M")
        return None

    def export_schedule_text(self) -> str:
        """Return today's schedule as a plain-text block suitable for copying."""
        today = date.today().isoformat()
        lines = [f"PawPal+ Schedule for {today}", "=" * 40]
        schedule = self.get_todays_schedule()
        if not schedule:
            lines.append("No tasks scheduled for today.")
        else:
            for task in schedule:
                status = "DONE" if task.completed else "PENDING"
                lines.append(
                    f"{task.time}  [{status}]  {task.description}  "
                    f"({task.duration_minutes} min, {task.priority})"
                )
        lines.append("")
        plan = self.build_daily_plan()
        if plan:
            lines.append("Recommended Plan:")
            for item in plan:
                lines.append(f"  {item['time']}  {item['description']}  - {item['reason']}")
        return "\n".join(lines)
