from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(tasks: list[Task]) -> None:
    """Print a readable schedule for terminal output."""
    print("Today's Schedule")
    print("-" * 92)
    print(f"{'Time':<8} {'Task':<25} {'Dur':<5} {'Prio':<7} {'Freq':<10} {'Due Date':<12} {'Done'}")
    print("-" * 92)
    for task in tasks:
        status = "✅" if task.completed else "⏳"
        priority_flag = "🔴" if task.priority == "high" else "🟡" if task.priority == "medium" else "🟢"
        print(
            f"{task.time:<8} {task.description:<25} {task.duration_minutes:<5} {priority_flag} {task.priority:<5} {task.frequency:<10} "
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
    owner = Owner(name="Jordan", daily_time_available=60, preferred_task_types=["walk", "meds"])

    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")

    # Add tasks in mixed order to verify sorting.
    dog.add_task(Task(description="Lunch feed", time="12:00", frequency="daily", duration_minutes=20, priority="medium"))
    dog.add_task(Task(description="Morning walk", time="08:00", frequency="daily", duration_minutes=30, priority="high"))
    cat.add_task(Task(description="Evening meds", time="19:30", frequency="daily", duration_minutes=10, priority="high"))
    cat.add_task(Task(description="Playtime", time="08:00", frequency="weekly", duration_minutes=25, priority="low"))

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

    print()
    print("Daily explainable plan")
    for item in scheduler.build_daily_plan():
        print(f"- {item['time']} {item['description']} ({item['priority']}, {item['duration_minutes']} min)")
        print(f"  Reason: {item['reason']}")

    print()
    slot = scheduler.next_available_slot(duration_minutes=20)
    print(f"Next available 20-minute slot: {slot}")


if __name__ == "__main__":
    main()
