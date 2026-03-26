from datetime import timedelta

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
    pet.add_task(Task(description="Noon meal", time="12:00", frequency="daily"))
    pet.add_task(Task(description="Morning walk", time="08:00", frequency="daily"))
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
    pet.add_task(Task(description="Morning walk", time="08:00", frequency="daily"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)

    changed = scheduler.mark_task_complete("Mochi", "Morning walk", "08:00")

    assert changed is True
    assert len(pet.tasks) == 2
    assert pet.tasks[0].completed is True
    assert pet.tasks[1].completed is False
    assert pet.tasks[1].due_date == pet.tasks[0].due_date + timedelta(days=1)


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
