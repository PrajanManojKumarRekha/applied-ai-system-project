from datetime import timedelta
from pathlib import Path

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def test_task_completion_changes_status() -> None:
    task = Task(description="Morning walk", time="08:00", frequency="daily")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_to_pet_increases_count() -> None:
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(description="Evening feed", time="18:00", frequency="daily"))

    assert len(pet.tasks) == 1


def test_scheduler_sorts_tasks_by_time() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(description="Noon meal", time="12:00", frequency="daily", priority="low"))
    pet.add_task(Task(description="Morning walk", time="08:00", frequency="daily", priority="high"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.get_todays_schedule()

    assert [task.time for task in schedule] == ["08:00", "12:00"]


def test_scheduler_filters_by_pet_and_status() -> None:
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")

    done_task = Task(description="Morning walk", time="08:00", frequency="daily", completed=True)
    dog.add_task(done_task)
    dog.add_task(Task(description="Lunch feed", time="12:00", frequency="daily"))
    cat.add_task(Task(description="Evening meds", time="19:30", frequency="daily"))

    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner=owner)
    filtered = scheduler.filter_tasks(pet_name="Mochi", completed=False)

    assert len(filtered) == 1
    assert filtered[0][0] == "Mochi"
    assert filtered[0][1].description == "Lunch feed"


def test_mark_complete_creates_next_daily_task() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(
        Task(
            description="Morning walk",
            time="08:00",
            frequency="daily",
            duration_minutes=20,
            priority="high",
        )
    )
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)

    changed = scheduler.mark_task_complete("Mochi", "Morning walk", "08:00")

    assert changed is True
    assert len(pet.tasks) == 2
    assert pet.tasks[0].completed is True
    assert pet.tasks[1].completed is False
    assert pet.tasks[1].due_date == pet.tasks[0].due_date + timedelta(days=1)
    assert pet.tasks[1].duration_minutes == pet.tasks[0].duration_minutes
    assert pet.tasks[1].priority == pet.tasks[0].priority


def test_detect_conflicts_returns_warning() -> None:
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    dog.add_task(Task(description="Morning walk", time="08:00", frequency="daily"))
    cat.add_task(Task(description="Breakfast", time="08:00", frequency="daily"))
    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "Conflict at 08:00" in warnings[0]


def test_pet_with_no_tasks_returns_empty_schedule() -> None:
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.get_todays_schedule()

    assert schedule == []


def test_build_daily_plan_uses_priority_and_time_budget() -> None:
    owner = Owner(name="Jordan", daily_time_available=45)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(
        Task(
            description="Morning walk",
            time="08:00",
            frequency="daily",
            duration_minutes=30,
            priority="high",
        )
    )
    pet.add_task(
        Task(
            description="Long grooming",
            time="09:00",
            frequency="weekly",
            duration_minutes=40,
            priority="low",
        )
    )
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    plan = scheduler.build_daily_plan()

    assert len(plan) == 1
    assert plan[0]["description"] == "Morning walk"
    assert "Selected Morning walk" in plan[0]["reason"]


def test_build_daily_plan_is_returned_in_time_order() -> None:
    owner = Owner(name="Jordan", daily_time_available=120)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(description="Evening meds", time="19:30", frequency="daily", priority="high"))
    pet.add_task(Task(description="Morning walk", time="08:00", frequency="daily", priority="medium"))
    pet.add_task(Task(description="Lunch feed", time="12:00", frequency="daily", priority="low"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    plan = scheduler.build_daily_plan()

    assert [item["time"] for item in plan] == ["08:00", "12:00", "19:30"]


def test_invalid_task_time_raises_value_error() -> None:
    with pytest.raises(ValueError):
        Task(description="Bad time", time="25:61", frequency="daily")


def test_duplicate_pet_name_raises_value_error() -> None:
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))

    with pytest.raises(ValueError):
        owner.add_pet(Pet(name="Mochi", species="cat"))


def test_next_available_slot_returns_open_time() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(
        Task(
            description="Morning walk",
            time="08:00",
            frequency="daily",
            duration_minutes=30,
            priority="high",
        )
    )
    pet.add_task(
        Task(
            description="Lunch feed",
            time="12:00",
            frequency="daily",
            duration_minutes=20,
            priority="medium",
        )
    )
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    slot = scheduler.next_available_slot(duration_minutes=15, start_time="08:30", end_time="11:00")

    assert slot == "08:30"


def test_owner_save_and_load_json_round_trip(tmp_path: Path) -> None:
    data_file = tmp_path / "data.json"

    owner = Owner(name="Jordan", daily_time_available=90, preferred_task_types=["walk"])
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(
        Task(
            description="Morning walk",
            time="08:00",
            frequency="daily",
            duration_minutes=30,
            priority="high",
        )
    )
    owner.add_pet(pet)
    owner.save_to_json(str(data_file))

    restored = Owner.load_from_json(str(data_file))

    assert restored.name == "Jordan"
    assert restored.daily_time_available == 90
    assert restored.preferred_task_types == ["walk"]
    assert len(restored.pets) == 1
    assert restored.pets[0].name == "Mochi"
    assert len(restored.pets[0].tasks) == 1
    assert restored.pets[0].tasks[0].priority == "high"
