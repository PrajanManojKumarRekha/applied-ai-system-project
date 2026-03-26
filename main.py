from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(tasks: list[Task]) -> None:
    """Print a readable schedule for terminal output."""
    print("Today's Schedule")
    print("-" * 60)
    print(f"{'Time':<8} {'Pet Task':<35} {'Freq':<10} {'Done'}")
    print("-" * 60)
    for task in tasks:
        status = "Yes" if task.completed else "No"
        print(f"{task.time:<8} {task.description:<35} {task.frequency:<10} {status}")


def main() -> None:
    """Create sample data and print today's schedule."""
    owner = Owner(name="Jordan")

    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")

    dog.add_task(Task(description="Morning walk", time="08:00", frequency="daily"))
    dog.add_task(Task(description="Lunch feed", time="12:00", frequency="daily"))
    cat.add_task(Task(description="Evening meds", time="19:30", frequency="daily"))

    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner=owner)
    schedule = scheduler.get_todays_schedule()

    print_schedule(schedule)


if __name__ == "__main__":
    main()
