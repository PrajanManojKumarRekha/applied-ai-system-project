from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(tasks: list[Task]) -> None:
    """Print a readable schedule for terminal output."""
    print("Today's Schedule")
    print("-" * 72)
    print(f"{'Time':<8} {'Task':<25} {'Freq':<10} {'Due Date':<12} {'Done'}")
    print("-" * 72)
    for task in tasks:
        status = "Yes" if task.completed else "No"
        print(
            f"{task.time:<8} {task.description:<25} {task.frequency:<10} "
            f"{task.due_date.isoformat():<12} {status}"
        )


def print_filtered(label: str, items: list[tuple[str, Task]]) -> None:
    """Print filtered task results with pet names."""
    print(label)
    print("-" * 72)
    print(f"{'Time':<8} {'Pet':<12} {'Task':<25} {'Done'}")
    print("-" * 72)
    for pet_name, task in items:
        status = "Yes" if task.completed else "No"
        print(f"{task.time:<8} {pet_name:<12} {task.description:<25} {status}")


def main() -> None:
    """Create sample data and print sorted, filtered, and conflict-aware schedules."""
    owner = Owner(name="Jordan")

    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")

    # Add tasks in mixed order to verify sorting.
    dog.add_task(Task(description="Lunch feed", time="12:00", frequency="daily"))
    dog.add_task(Task(description="Morning walk", time="08:00", frequency="daily"))
    cat.add_task(Task(description="Evening meds", time="19:30", frequency="daily"))
    cat.add_task(Task(description="Playtime", time="08:00", frequency="weekly"))

    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner=owner)

    print()
    schedule = scheduler.get_todays_schedule()
    print_schedule(schedule)

    print()
    pending_for_mochi = scheduler.filter_tasks(pet_name="Mochi", completed=False)
    print_filtered("Pending tasks for Mochi", pending_for_mochi)

    print()
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        print("Conflict warnings")
        for warning in conflicts:
            print(f"- {warning}")
    else:
        print("No conflicts found")

    # Complete a recurring task and show the new instance.
    scheduler.mark_task_complete("Mochi", "Morning walk", "08:00")
    print()
    print("After completing Mochi's Morning walk")
    mochi = owner.get_pet_by_name("Mochi")
    if mochi is not None:
        print_schedule(scheduler.sort_by_time(mochi.tasks))


if __name__ == "__main__":
    main()
