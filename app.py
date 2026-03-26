import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

DATA_FILE = "data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown("Plan pet care tasks and build Today's schedule.")

# Keep one Owner object in session state so data persists across reruns.
if "owner" not in st.session_state:
    try:
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
    except Exception:
        st.session_state.owner = Owner(name="Jordan")
if "daily_minutes_ui" not in st.session_state:
    st.session_state.daily_minutes_ui = st.session_state.owner.daily_time_available


def save_owner_state() -> None:
    """Persist owner data so pets and tasks survive app restarts."""
    st.session_state.owner.save_to_json(DATA_FILE)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner And Pets")
owner_name = st.text_input("Owner Name", value=st.session_state.owner.name)
if st.session_state.owner.name != owner_name:
    st.session_state.owner.name = owner_name
    save_owner_state()
daily_minutes = st.number_input(
    "Daily Time Available (Minutes)",
    min_value=30,
    max_value=1440,
    step=1,
    key="daily_minutes_ui",
)
if st.session_state.owner.daily_time_available != int(daily_minutes):
    st.session_state.owner.set_daily_time_available(int(daily_minutes))
    save_owner_state()

preferences_text = st.text_input(
    "Preferred Task Keywords (Comma Separated)",
    value=", ".join(st.session_state.owner.preferred_task_types),
)
parsed_preferences = [item.strip() for item in preferences_text.split(",") if item.strip()]
if parsed_preferences != st.session_state.owner.preferred_task_types:
    st.session_state.owner.set_preferences(parsed_preferences)
    save_owner_state()

with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet Name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    care_notes = st.text_input("Care Notes", value="")
    add_pet_submit = st.form_submit_button("Add Pet")

if add_pet_submit:
    clean_pet_name = pet_name.strip()
    if not clean_pet_name:
        st.error("Please enter a pet name.")
    else:
        try:
            st.session_state.owner.add_pet(
                Pet(name=clean_pet_name, species=species, care_notes=care_notes.strip())
            )
            st.success(f"Added pet: {clean_pet_name}")
            save_owner_state()
        except ValueError as exc:
            st.error(str(exc))

if st.session_state.owner.pets:
    st.write("Current Pets")
    st.table(
        [
            {
                "Name": pet.name,
                "Species": pet.species,
                "Care Notes": pet.care_notes,
                "Task Count": len(pet.tasks),
            }
            for pet in st.session_state.owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
st.caption("Add a task to one of your pets.")

if st.session_state.owner.pets:
    pet_lookup = {pet.name: pet for pet in st.session_state.owner.pets}
    with st.form("add_task_form", clear_on_submit=True):
        selected_pet_name = st.selectbox("Select Pet", list(pet_lookup.keys()))
        task_description = st.text_input("Task Description", value="Morning walk")
        task_time = st.time_input("Task Time")
        duration_minutes = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=30)
        priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])
        add_task_submit = st.form_submit_button("Add Task")

    if add_task_submit:
        clean_task_description = task_description.strip()
        if not clean_task_description:
            st.error("Please enter a task description.")
        else:
            selected_pet = pet_lookup[selected_pet_name]
            try:
                selected_pet.add_task(
                    Task(
                        description=clean_task_description,
                        time=task_time.strftime("%H:%M"),
                        frequency=frequency,
                        duration_minutes=int(duration_minutes),
                        priority=priority,
                    )
                )
                st.success(f"Added task to {selected_pet_name}: {clean_task_description}")
                save_owner_state()
            except (ValueError, TypeError) as exc:
                st.error(str(exc))

all_tasks = []
for pet in st.session_state.owner.pets:
    for task in pet.tasks:
        all_tasks.append(
            {
                "pet": pet.name,
                "description": task.description,
                "time": task.time,
                "duration_minutes": task.duration_minutes,
                "priority": task.priority,
                "frequency": task.frequency,
                "completed": task.completed,
            }
        )

if all_tasks:
    st.write("Current Tasks")
    st.table(
        [
            {
                "Pet": row["pet"],
                "Description": row["description"],
                "Time": row["time"],
                "Duration Minutes": row["duration_minutes"],
                "Priority": row["priority"],
                "Priority Flag": (
                    "🔴 High"
                    if row["priority"] == "high"
                    else "🟡 Medium" if row["priority"] == "medium" else "🟢 Low"
                ),
                "Frequency": row["frequency"],
                "Completed": row["completed"],
                "Status": "✅ Done" if row["completed"] else "⏳ Pending",
            }
            for row in all_tasks
        ]
    )
else:
    st.info("No tasks yet. Add a pet, then add tasks.")

st.divider()

st.subheader("View And Filter Tasks")

if st.session_state.owner.pets:
    scheduler = Scheduler(owner=st.session_state.owner)
    pet_options = ["All Pets"] + [pet.name for pet in st.session_state.owner.pets]
    selected_pet_filter = st.selectbox("Filter By Pet", pet_options)
    status_filter = st.selectbox(
        "Filter By Status",
        ["All", "Pending", "Completed"],
    )

    filter_pet_name = None if selected_pet_filter == "All Pets" else selected_pet_filter
    if status_filter == "All":
        filter_completed = None
    elif status_filter == "Pending":
        filter_completed = False
    else:
        filter_completed = True

    filtered_items = scheduler.filter_tasks(pet_name=filter_pet_name, completed=filter_completed)
    filtered_rows = [
        {
            "Pet": pet_name,
            "Time": task.time,
            "Description": task.description,
            "Duration Minutes": task.duration_minutes,
            "Priority": task.priority,
            "Frequency": task.frequency,
            "Due Date": task.due_date.isoformat(),
            "Completed": task.completed,
        }
        for pet_name, task in filtered_items
    ]

    if filtered_rows:
        st.success(f"Showing {len(filtered_rows)} task(s) with active filters.")
        st.table(filtered_rows)

        task_option_map = {}
        task_options = []
        for pet_name, task in filtered_items:
            label = (
                f"{pet_name} | {task.time} | {task.description} | "
                f"{task.due_date.isoformat()} | Completed: {task.completed}"
            )
            task_options.append(label)
            task_option_map[label] = task

        st.markdown("#### Update Task Status")
        selected_task_label = st.selectbox("Select Task", task_options, key="task_status_selector")
        selected_task = task_option_map[selected_task_label]

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Mark As Completed") and selected_task is not None:
                selected_task.mark_complete()
                st.success("Task marked as completed.")
                save_owner_state()
                st.rerun()
        with col2:
            if st.button("Mark As Pending") and selected_task is not None:
                selected_task.mark_incomplete()
                st.success("Task marked as pending.")
                save_owner_state()
                st.rerun()
    else:
        st.info("No tasks match this filter.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate today's schedule from all pet tasks using priority and time constraints.")

slot_duration = st.number_input("Next Slot Duration (Minutes)", min_value=1, max_value=240, value=30)
slot_pet_options = ["All Pets"] + [pet.name for pet in st.session_state.owner.pets]
slot_pet_choice = st.selectbox("Find Slot For", slot_pet_options)

if st.button("Generate schedule"):
    if not st.session_state.owner.pets:
        st.warning("Add at least one pet first.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner)
        schedule = scheduler.get_todays_schedule()
        if not schedule:
            st.info("No tasks available for today.")
        else:
            st.write("Today's Sorted Schedule")
            st.table(
                [
                    {
                        "Time": task.time,
                        "Description": task.description,
                        "Duration Minutes": task.duration_minutes,
                        "Priority": task.priority,
                        "Priority Flag": (
                            "🔴 High" if task.priority == "high" else "🟡 Medium" if task.priority == "medium" else "🟢 Low"
                        ),
                        "Frequency": task.frequency,
                        "Due Date": task.due_date.isoformat(),
                        "Done": task.completed,
                        "Status": "✅ Done" if task.completed else "⏳ Pending",
                    }
                    for task in schedule
                ]
            )

        daily_plan = scheduler.build_daily_plan()
        if daily_plan:
            st.write("Daily Plan With Reasoning")
            st.table(
                [
                    {
                        "Time": item["time"],
                        "Description": item["description"],
                        "Priority": item["priority"],
                        "Duration Minutes": item["duration_minutes"],
                        "Reason": item["reason"],
                    }
                    for item in daily_plan
                ]
            )
        else:
            st.info("No tasks fit the current time budget.")

        warnings = scheduler.detect_conflicts()
        if warnings:
            st.warning("Task conflicts found. Review these before starting your day.")
            for warning in warnings:
                st.warning(warning)
        else:
            st.success("No task conflicts found for pending tasks.")

        next_slot = scheduler.next_available_slot(
            duration_minutes=int(slot_duration),
            pet_name=None if slot_pet_choice == "All Pets" else slot_pet_choice,
        )
        if next_slot is None:
            st.info("No open slot found for the selected duration.")
        else:
            st.success(f"Next available slot: {next_slot}")
