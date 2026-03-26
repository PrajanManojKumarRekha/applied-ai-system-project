from pawpal_system import Pet, Task


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
