const pawpalClassDiagram = `classDiagram
    class Owner {
        +name: str
        +daily_time_available: int
        +preferred_task_types: List~str~
        +pets: List~Pet~
        +add_pet(pet)
        +set_daily_time_available(minutes)
        +set_preferences(preferred_task_types)
        +get_pet_by_name(pet_name) Pet
        +get_all_tasks() List~Task~
        +get_all_pending_tasks() List~Task~
        +save_to_json(file_path)
        +load_from_json(file_path) Owner
    }

    class Pet {
        +name: str
        +species: str
        +care_notes: str
        +tasks: List~Task~
        +update_notes(notes)
        +add_task(task)
        +get_tasks() List~Task~
        +get_pending_tasks() List~Task~
    }

    class Task {
        +description: str
        +time: str
        +frequency: str
        +duration_minutes: int
        +priority: str
        +due_date: date
        +completed: bool
        +mark_complete()
        +mark_incomplete()
    }

    class Scheduler {
        +owner: Owner
        +get_all_tasks() List~Task~
        +sort_by_time(tasks) List~Task~
        +sort_by_priority_then_time(tasks) List~Task~
        +score_task(task) int
        +filter_tasks(pet_name, completed) List
        +get_todays_schedule() List~Task~
        +get_pending_schedule() List~Task~
        +build_daily_plan(daily_minutes_available, pet_name) List
        +explain_plan(plan) List~str~
        +mark_task_complete(pet_name, task_description, task_time) bool
        +detect_conflicts() List~str~
        +next_available_slot(duration_minutes, target_date, start_time, end_time, pet_name) str
    }

    Owner "1" --> "0..*" Pet : has
    Pet "1" --> "0..*" Task : stores
    Scheduler "1" --> "1" Owner : reads
    Scheduler ..> Task : sorts and filters`;

export default pawpalClassDiagram;
