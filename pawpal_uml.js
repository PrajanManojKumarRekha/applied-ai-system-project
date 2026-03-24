const pawpalClassDiagram = `classDiagram
    class Owner {
        +name: str
        +daily_time_available: int
        +preferred_task_types: list
        +add_pet(pet)
        +add_task(task)
        +set_time_limit(minutes)
    }

    class Pet {
        +name: str
        +species: str
        +care_notes: str
        +update_notes(notes)
    }

    class Task {
        +title: str
        +category: str
        +duration_minutes: int
        +priority: str
        +required: bool
        +mark_done()
        +fits_in(remaining_minutes) bool
    }

    class Scheduler {
        +time_limit_minutes: int
        +score_task(task) int
        +build_plan(owner) list
        +explain_plan(plan) list
    }

    Owner "1" --> "0..*" Pet : has
    Owner "1" --> "0..*" Task : manages
    Scheduler ..> Owner : uses
    Scheduler ..> Task : schedules`;

export default pawpalClassDiagram;
