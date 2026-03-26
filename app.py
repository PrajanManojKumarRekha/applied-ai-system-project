import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown("Plan pet care tasks and build today's schedule.")

# Keep one Owner object in session state so data persists across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")

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

st.subheader("Owner and Pets")
owner_name = st.text_input("Owner name", value=st.session_state.owner.name)
st.session_state.owner.name = owner_name

with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    care_notes = st.text_input("Care notes", value="")
    add_pet_submit = st.form_submit_button("Add pet")

if add_pet_submit:
    clean_pet_name = pet_name.strip()
    if not clean_pet_name:
        st.error("Please enter a pet name.")
    else:
        st.session_state.owner.add_pet(
            Pet(name=clean_pet_name, species=species, care_notes=care_notes.strip())
        )
        st.success(f"Added pet: {clean_pet_name}")

if st.session_state.owner.pets:
    st.write("Current pets:")
    st.table(
        [
            {
                "name": pet.name,
                "species": pet.species,
                "care_notes": pet.care_notes,
                "task_count": len(pet.tasks),
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
        selected_pet_name = st.selectbox("Select pet", list(pet_lookup.keys()))
        task_description = st.text_input("Task description", value="Morning walk")
        task_time = st.time_input("Task time")
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])
        add_task_submit = st.form_submit_button("Add task")

    if add_task_submit:
        clean_task_description = task_description.strip()
        if not clean_task_description:
            st.error("Please enter a task description.")
        else:
            selected_pet = pet_lookup[selected_pet_name]
            selected_pet.add_task(
                Task(
                    description=clean_task_description,
                    time=task_time.strftime("%H:%M"),
                    frequency=frequency,
                )
            )
            st.success(f"Added task to {selected_pet_name}: {clean_task_description}")

all_tasks = []
for pet in st.session_state.owner.pets:
    for task in pet.tasks:
        all_tasks.append(
            {
                "pet": pet.name,
                "description": task.description,
                "time": task.time,
                "frequency": task.frequency,
                "completed": task.completed,
            }
        )

if all_tasks:
    st.write("Current tasks:")
    st.table(all_tasks)
else:
    st.info("No tasks yet. Add a pet, then add tasks.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate today's schedule from all pet tasks.")

if st.button("Generate schedule"):
    if not st.session_state.owner.pets:
        st.warning("Add at least one pet first.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner)
        schedule = scheduler.get_todays_schedule()
        if not schedule:
            st.info("No tasks available for today.")
        else:
            st.write("Today's Schedule")
            st.table(
                [
                    {
                        "time": task.time,
                        "description": task.description,
                        "frequency": task.frequency,
                        "done": task.completed,
                    }
                    for task in schedule
                ]
            )
