import streamlit as st
from datetime import date

from ai_advisor import AdvisorResult, get_care_advice
from pawpal_system import HealthRecord, Owner, Pet, Scheduler, Task

DATA_FILE = "data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ------------------------------------------------------------------ #
#  Session state init                                                  #
# ------------------------------------------------------------------ #
if "owner" not in st.session_state:
    try:
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
    except Exception:
        st.session_state.owner = Owner(name="Jordan")

if "daily_minutes_ui" not in st.session_state:
    st.session_state.daily_minutes_ui = st.session_state.owner.daily_time_available

if "advice_history" not in st.session_state:
    st.session_state.advice_history = []


def save_owner_state() -> None:
    st.session_state.owner.save_to_json(DATA_FILE)


# ------------------------------------------------------------------ #
#  Sidebar: owner stats dashboard                                      #
# ------------------------------------------------------------------ #
with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Pet care scheduling + AI advisor")
    st.divider()

    owner = st.session_state.owner
    total_tasks = len(owner.get_all_tasks())
    completed_tasks = sum(1 for t in owner.get_all_tasks() if t.completed)
    pending_tasks = total_tasks - completed_tasks
    rate = owner.completion_rate()
    mins_done = owner.total_minutes_completed()
    mins_budget = owner.daily_time_available

    st.subheader("Stats")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Pets", len(owner.pets))
        st.metric("Total Tasks", total_tasks)
    with col_b:
        st.metric("Done Today", completed_tasks)
        st.metric("Pending", pending_tasks)

    st.metric("Completion Rate", f"{int(rate * 100)}%")
    st.progress(rate)

    st.metric("Time Used (all tasks)", f"{mins_done} min / {mins_budget} min")

    if owner.pets:
        st.divider()
        st.subheader("Streaks")
        for pet in owner.pets:
            streak = pet.streak_days
            label = f"{pet.name}"
            if streak >= 7:
                label += " 🔥"
            elif streak >= 3:
                label += " ✨"
            st.metric(label, f"{streak} day{'s' if streak != 1 else ''}")

    st.divider()
    st.caption(f"Data saved to `{DATA_FILE}`")


# ------------------------------------------------------------------ #
#  Main tabs                                                           #
# ------------------------------------------------------------------ #
st.header("PawPal+")
tabs = st.tabs(["Pets and Tasks", "Health Log", "Build Schedule", "AI Advisor"])

# ------------------------------------------------------------------ #
#  Tab 1: Pets and Tasks                                               #
# ------------------------------------------------------------------ #
with tabs[0]:
    st.subheader("Owner Settings")

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

    st.divider()
    st.subheader("Add a Pet")

    with st.form("add_pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet Name")
        species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
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
                    "Streak (days)": pet.streak_days,
                }
                for pet in st.session_state.owner.pets
            ]
        )
    else:
        st.info("No pets yet. Add one above.")

    st.divider()
    st.subheader("Add a Task")

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
        st.write("All Tasks")
        st.table(
            [
                {
                    "Pet": row["pet"],
                    "Description": row["description"],
                    "Time": row["time"],
                    "Duration (min)": row["duration_minutes"],
                    "Priority": row["priority"].capitalize(),
                    "Frequency": row["frequency"],
                    "Status": "Done" if row["completed"] else "Pending",
                }
                for row in all_tasks
            ]
        )
    else:
        st.info("No tasks yet. Add a pet, then add tasks.")

    st.divider()
    st.subheader("Filter and Update Tasks")

    if st.session_state.owner.pets:
        scheduler = Scheduler(owner=st.session_state.owner)
        pet_options = ["All Pets"] + [pet.name for pet in st.session_state.owner.pets]
        selected_pet_filter = st.selectbox("Filter By Pet", pet_options)
        status_filter = st.selectbox("Filter By Status", ["All", "Pending", "Completed"])

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
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Frequency": task.frequency,
                "Due Date": task.due_date.isoformat(),
                "Status": "Done" if task.completed else "Pending",
            }
            for pet_name, task in filtered_items
        ]

        if filtered_rows:
            st.success(f"Showing {len(filtered_rows)} task(s).")
            st.table(filtered_rows)

            task_option_map = {}
            task_options = []
            for pet_name, task in filtered_items:
                label = (
                    f"{pet_name} | {task.time} | {task.description} | "
                    f"{task.due_date.isoformat()} | {('Done' if task.completed else 'Pending')}"
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


# ------------------------------------------------------------------ #
#  Tab 2: Health Log                                                   #
# ------------------------------------------------------------------ #
with tabs[1]:
    st.subheader("Pet Health Log")
    st.caption("Track vaccinations, vet visits, and other health events for each pet.")

    if not st.session_state.owner.pets:
        st.info("Add at least one pet first.")
    else:
        pet_lookup_health = {pet.name: pet for pet in st.session_state.owner.pets}

        with st.form("add_health_record_form", clear_on_submit=True):
            health_pet = st.selectbox("Select Pet", list(pet_lookup_health.keys()), key="health_pet_select")
            record_type = st.selectbox(
                "Record Type",
                ["vaccination", "vet visit", "medication", "surgery", "checkup", "other"],
            )
            record_description = st.text_input("Description", placeholder="Rabies vaccine, annual checkup...")
            record_date = st.date_input("Date", value=date.today())
            record_notes = st.text_area("Notes (optional)", height=60)
            add_record_submit = st.form_submit_button("Add Health Record")

        if add_record_submit:
            clean_desc = record_description.strip()
            if not clean_desc:
                st.error("Please enter a description.")
            else:
                try:
                    pet_lookup_health[health_pet].add_health_record(
                        HealthRecord(
                            record_type=record_type,
                            description=clean_desc,
                            record_date=record_date,
                            notes=record_notes.strip(),
                        )
                    )
                    st.success(f"Health record added for {health_pet}.")
                    save_owner_state()
                except Exception as exc:
                    st.error(str(exc))

        st.divider()
        view_pet = st.selectbox("View Records For", list(pet_lookup_health.keys()), key="health_view_select")
        selected_pet_obj = pet_lookup_health[view_pet]
        records = selected_pet_obj.get_health_records()

        if records:
            st.write(f"Health History for {view_pet} ({len(records)} record(s))")
            st.table(
                [
                    {
                        "Date": r.record_date.isoformat(),
                        "Type": r.record_type.capitalize(),
                        "Description": r.description,
                        "Notes": r.notes or "-",
                    }
                    for r in records
                ]
            )
        else:
            st.info(f"No health records yet for {view_pet}.")


# ------------------------------------------------------------------ #
#  Tab 3: Build Schedule                                               #
# ------------------------------------------------------------------ #
with tabs[2]:
    st.subheader("Build Schedule")
    st.caption("Generate today's schedule from all pet tasks using priority and time constraints.")

    slot_duration = st.number_input("Next Slot Duration (Minutes)", min_value=1, max_value=240, value=30)
    slot_pet_options = ["All Pets"] + [pet.name for pet in st.session_state.owner.pets]
    slot_pet_choice = st.selectbox("Find Slot For", slot_pet_options)

    if st.button("Generate Schedule"):
        if not st.session_state.owner.pets:
            st.warning("Add at least one pet first.")
        else:
            scheduler = Scheduler(owner=st.session_state.owner)
            schedule = scheduler.get_todays_schedule()
            if not schedule:
                st.info("No tasks scheduled for today.")
            else:
                st.write("Today's Sorted Schedule")
                st.table(
                    [
                        {
                            "Time": task.time,
                            "Description": task.description,
                            "Duration (min)": task.duration_minutes,
                            "Priority": task.priority.capitalize(),
                            "Frequency": task.frequency,
                            "Due Date": task.due_date.isoformat(),
                            "Status": "Done" if task.completed else "Pending",
                        }
                        for task in schedule
                    ]
                )

            daily_plan = scheduler.build_daily_plan()
            if daily_plan:
                st.write("Recommended Daily Plan")
                st.table(
                    [
                        {
                            "Time": item["time"],
                            "Description": item["description"],
                            "Priority": item["priority"].capitalize(),
                            "Duration (min)": item["duration_minutes"],
                            "Reason": item["reason"],
                        }
                        for item in daily_plan
                    ]
                )
            else:
                st.info("No tasks fit the current time budget.")

            warnings = scheduler.detect_conflicts()
            if warnings:
                st.warning("Schedule conflicts found:")
                for warning in warnings:
                    st.warning(warning)
            else:
                st.success("No conflicts found for pending tasks.")

            next_slot = scheduler.next_available_slot(
                duration_minutes=int(slot_duration),
                pet_name=None if slot_pet_choice == "All Pets" else slot_pet_choice,
            )
            if next_slot is None:
                st.info("No open slot found for the selected duration.")
            else:
                st.success(f"Next available slot: {next_slot}")

            st.divider()
            st.subheader("Export Schedule")
            export_text = scheduler.export_schedule_text()
            st.text_area("Copy this text", value=export_text, height=200, key="export_text_area")
            st.download_button(
                label="Download as .txt",
                data=export_text,
                file_name=f"pawpal_schedule_{date.today().isoformat()}.txt",
                mime="text/plain",
            )


# ------------------------------------------------------------------ #
#  Tab 4: AI Advisor                                                   #
# ------------------------------------------------------------------ #
with tabs[3]:
    st.subheader("AI Advisor")
    st.caption(
        "Ask the AI to review your pet's schedule and suggest improvements. "
        "Advice includes a confidence score and a guardrail flag."
    )

    user_question = st.text_area(
        "Optional Question",
        placeholder="Example: Is my dog getting enough exercise? Are any tasks missing?",
        height=80,
    )

    if st.button("Get AI Advice"):
        if not st.session_state.owner.pets:
            st.warning("Add at least one pet and some tasks before asking for advice.")
        else:
            with st.spinner("Asking Groq for care advice..."):
                try:
                    result: AdvisorResult = get_care_advice(
                        owner_data=st.session_state.owner.to_dict(),
                        user_question=user_question.strip() or None,
                    )
                except ValueError as exc:
                    st.error(f"Could not reach the AI advisor: {exc}")
                    result = None

            if result is not None:
                st.session_state.advice_history.insert(0, {
                    "timestamp": date.today().isoformat(),
                    "question": user_question.strip() or "(no question)",
                    "result": result,
                })
                st.session_state.advice_history = st.session_state.advice_history[:3]

                col_conf, col_flag = st.columns(2)
                with col_conf:
                    pct = int(result.confidence * 100)
                    st.metric("Confidence", f"{pct}%")
                with col_flag:
                    flag_labels = {
                        "none": "All Clear",
                        "missing_vet": "Missing Vet Visit",
                        "overloaded": "Schedule Overloaded",
                        "incomplete_data": "Incomplete Data",
                    }
                    flag_text = flag_labels.get(result.flag, result.flag)
                    st.metric("Flag", flag_text)
                    if not result.is_safe:
                        st.warning(f"Guardrail triggered: {result.flag}")

                st.markdown("**Summary**")
                st.info(result.summary)

                st.markdown("**Suggestions**")
                for i, suggestion in enumerate(result.suggestions, start=1):
                    st.markdown(f"{i}. {suggestion}")

                with st.expander("Raw JSON response"):
                    st.code(result.raw_response, language="json")

    if st.session_state.advice_history:
        st.divider()
        st.subheader("Recent Advice History")
        for i, entry in enumerate(st.session_state.advice_history):
            r = entry["result"]
            label = f"Run {i + 1} ({entry['timestamp']}) - {int(r.confidence * 100)}% confidence - {r.flag}"
            with st.expander(label, expanded=(i == 0)):
                st.caption(f"Question: {entry['question']}")
                st.markdown(f"**Summary:** {r.summary}")
                for j, s in enumerate(r.suggestions, 1):
                    st.markdown(f"{j}. {s}")

    st.divider()
    st.markdown(
        "**How it works:** The AI Advisor sends your pet schedule to a Groq-hosted LLM, which "
        "identifies care gaps and returns structured suggestions with a self-rated confidence score. "
        "A guardrail layer validates the response format and flags unsafe or incomplete advice "
        "before it reaches you."
    )
