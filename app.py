import streamlit as st
from datetime import date

from ai_advisor import AdvisorResult, get_care_advice
from pawpal_system import HealthRecord, Owner, Pet, Scheduler, Task

OWNERS_FILE = "owners.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")


# ------------------------------------------------------------------ #
#  Session state init                                                  #
# ------------------------------------------------------------------ #
if "owners" not in st.session_state:
    st.session_state.owners = Owner.load_all(OWNERS_FILE)

if "active_owner_index" not in st.session_state:
    st.session_state.active_owner_index = 0

if "advice_history" not in st.session_state:
    st.session_state.advice_history = []


def save_all() -> None:
    Owner.save_all(st.session_state.owners, OWNERS_FILE)


def active_owner() -> Owner:
    idx = st.session_state.active_owner_index
    return st.session_state.owners[idx]


# ------------------------------------------------------------------ #
#  Sidebar                                                             #
# ------------------------------------------------------------------ #
with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Pet care scheduling + AI advisor")
    st.divider()

    # -- Owner switcher ------------------------------------------------
    st.subheader("Owners")
    owner_names = [o.name for o in st.session_state.owners]
    selected_name = st.selectbox(
        "Active Owner",
        owner_names,
        index=st.session_state.active_owner_index,
        key="sidebar_owner_select",
    )
    new_idx = owner_names.index(selected_name)
    if new_idx != st.session_state.active_owner_index:
        st.session_state.active_owner_index = new_idx
        st.rerun()

    with st.form("add_owner_form", clear_on_submit=True):
        new_owner_name = st.text_input("New Owner Name")
        add_owner_btn = st.form_submit_button("Add Owner")

    if add_owner_btn:
        name = new_owner_name.strip()
        if not name:
            st.error("Enter a name.")
        elif name in [o.name for o in st.session_state.owners]:
            st.error(f"Owner '{name}' already exists.")
        else:
            st.session_state.owners.append(Owner(name=name))
            st.session_state.active_owner_index = len(st.session_state.owners) - 1
            save_all()
            st.rerun()

    if len(st.session_state.owners) > 1:
        if st.button("Delete This Owner", type="secondary"):
            st.session_state.owners.pop(st.session_state.active_owner_index)
            st.session_state.active_owner_index = 0
            save_all()
            st.rerun()

    st.divider()

    # -- Stats for active owner ----------------------------------------
    owner = active_owner()
    total_tasks = len(owner.get_all_tasks())
    completed_count = sum(1 for t in owner.get_all_tasks() if t.completed)
    pending_count = total_tasks - completed_count
    rate = owner.completion_rate()
    mins_done = owner.total_minutes_completed()

    st.subheader(f"Stats: {owner.name}")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Pets", len(owner.pets))
        st.metric("Total Tasks", total_tasks)
    with col_b:
        st.metric("Completed", completed_count)
        st.metric("Pending", pending_count)

    st.metric("Completion Rate", f"{int(rate * 100)}%")
    st.progress(rate)
    st.metric("Time Logged", f"{mins_done} / {owner.daily_time_available} min")

    if owner.pets:
        st.divider()
        st.subheader("Streaks")
        for pet in owner.pets:
            streak = pet.streak_days
            label = pet.name
            if streak >= 7:
                label += " 🔥"
            elif streak >= 3:
                label += " ✨"
            st.metric(label, f"{streak} day{'s' if streak != 1 else ''}")

    st.divider()
    st.caption(f"Saved to `{OWNERS_FILE}`")


# ------------------------------------------------------------------ #
#  Main area                                                           #
# ------------------------------------------------------------------ #
st.header(f"PawPal+ — {active_owner().name}")
tabs = st.tabs(["Pets and Tasks", "Health Log", "Build Schedule", "AI Advisor"])


# ------------------------------------------------------------------ #
#  Tab 1: Pets and Tasks                                               #
# ------------------------------------------------------------------ #
with tabs[0]:
    owner = active_owner()

    # Owner settings
    st.subheader("Owner Settings")
    new_owner_display_name = st.text_input("Owner Name", value=owner.name, key="owner_name_input")
    if new_owner_display_name.strip() and new_owner_display_name.strip() != owner.name:
        owner.name = new_owner_display_name.strip()
        save_all()

    daily_minutes = st.number_input(
        "Daily Time Available (Minutes)",
        min_value=30,
        max_value=1440,
        step=1,
        value=owner.daily_time_available,
        key="daily_minutes_ui",
    )
    if owner.daily_time_available != int(daily_minutes):
        owner.set_daily_time_available(int(daily_minutes))
        save_all()

    preferences_text = st.text_input(
        "Preferred Task Keywords (Comma Separated)",
        value=", ".join(owner.preferred_task_types),
        key="preferences_input",
    )
    parsed_prefs = [p.strip() for p in preferences_text.split(",") if p.strip()]
    if parsed_prefs != owner.preferred_task_types:
        owner.set_preferences(parsed_prefs)
        save_all()

    st.divider()
    st.subheader(f"Add a Pet for {owner.name}")

    with st.form("add_pet_form", clear_on_submit=True):
        pet_name_input = st.text_input("Pet Name")
        species_input = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
        care_notes_input = st.text_input("Care Notes", value="")
        add_pet_btn = st.form_submit_button("Add Pet")

    if add_pet_btn:
        clean = pet_name_input.strip()
        if not clean:
            st.error("Please enter a pet name.")
        else:
            try:
                owner.add_pet(Pet(name=clean, species=species_input, care_notes=care_notes_input.strip()))
                st.success(f"Added {clean} to {owner.name}.")
                save_all()
            except ValueError as exc:
                st.error(str(exc))

    # All owners + their pets overview
    st.divider()
    st.subheader("All Owners and Pets")
    all_pet_rows = []
    for o in st.session_state.owners:
        for p in o.pets:
            all_pet_rows.append({
                "Owner": o.name,
                "Pet": p.name,
                "Species": p.species,
                "Care Notes": p.care_notes or "-",
                "Tasks": len(p.tasks),
                "Streak (days)": p.streak_days,
            })
    if all_pet_rows:
        st.table(all_pet_rows)
    else:
        st.info("No pets registered yet.")

    # Active owner's pets detail
    st.divider()
    st.subheader(f"{owner.name}'s Pets")
    if owner.pets:
        st.table([{
            "Pet": p.name,
            "Species": p.species,
            "Care Notes": p.care_notes or "-",
            "Tasks": len(p.tasks),
            "Streak (days)": p.streak_days,
        } for p in owner.pets])
    else:
        st.info(f"{owner.name} has no pets yet.")

    st.divider()
    st.subheader(f"Add a Task for {owner.name}'s Pets")

    if owner.pets:
        pet_lookup = {p.name: p for p in owner.pets}
        with st.form("add_task_form", clear_on_submit=True):
            sel_pet = st.selectbox("Select Pet", list(pet_lookup.keys()))
            task_desc = st.text_input("Task Description", value="Morning walk")
            task_time_input = st.time_input("Task Time")
            task_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=30)
            task_priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)
            task_frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])
            add_task_btn = st.form_submit_button("Add Task")

        if add_task_btn:
            clean_desc = task_desc.strip()
            if not clean_desc:
                st.error("Please enter a task description.")
            else:
                try:
                    pet_lookup[sel_pet].add_task(Task(
                        description=clean_desc,
                        time=task_time_input.strftime("%H:%M"),
                        frequency=task_frequency,
                        duration_minutes=int(task_duration),
                        priority=task_priority,
                    ))
                    st.success(f"Added '{clean_desc}' to {sel_pet}.")
                    save_all()
                except (ValueError, TypeError) as exc:
                    st.error(str(exc))
    else:
        st.info(f"Add a pet for {owner.name} first.")

    # Task list for active owner
    owner_tasks = []
    for p in owner.pets:
        for t in p.tasks:
            owner_tasks.append({
                "Owner": owner.name,
                "Pet": p.name,
                "Description": t.description,
                "Time": t.time,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority.capitalize(),
                "Frequency": t.frequency,
                "Status": "Done" if t.completed else "Pending",
            })

    if owner_tasks:
        st.divider()
        st.write(f"All Tasks for {owner.name}")
        st.table(owner_tasks)
    else:
        st.info("No tasks yet for this owner.")

    st.divider()
    st.subheader("Filter and Update Tasks")

    if owner.pets:
        scheduler = Scheduler(owner=owner)
        pet_filter_options = ["All Pets"] + [p.name for p in owner.pets]
        sel_pet_filter = st.selectbox("Filter By Pet", pet_filter_options, key="filter_pet")
        sel_status_filter = st.selectbox("Filter By Status", ["All", "Pending", "Completed"], key="filter_status")
        sel_priority_filter = st.selectbox("Filter By Priority", ["All", "High", "Medium", "Low"], key="filter_priority")

        filter_pet_name = None if sel_pet_filter == "All Pets" else sel_pet_filter
        filter_completed = None if sel_status_filter == "All" else (sel_status_filter == "Completed")

        filtered_items = scheduler.filter_tasks(pet_name=filter_pet_name, completed=filter_completed)

        if sel_priority_filter != "All":
            filtered_items = [
                (pn, t) for pn, t in filtered_items
                if t.priority == sel_priority_filter.lower()
            ]

        filtered_rows = [{
            "Pet": pn,
            "Time": t.time,
            "Description": t.description,
            "Duration (min)": t.duration_minutes,
            "Priority": t.priority.capitalize(),
            "Frequency": t.frequency,
            "Due Date": t.due_date.isoformat(),
            "Status": "Done" if t.completed else "Pending",
        } for pn, t in filtered_items]

        if filtered_rows:
            st.success(f"Showing {len(filtered_rows)} task(s).")
            st.table(filtered_rows)

            task_option_map = {}
            task_options = []
            for pn, t in filtered_items:
                label = f"{pn} | {t.time} | {t.description} | {t.due_date.isoformat()} | {'Done' if t.completed else 'Pending'}"
                task_options.append(label)
                task_option_map[label] = t

            st.markdown("#### Update Task Status")
            sel_label = st.selectbox("Select Task", task_options, key="task_status_selector")
            sel_task = task_option_map[sel_label]

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Mark As Completed"):
                    sel_task.mark_complete()
                    save_all()
                    st.rerun()
            with col2:
                if st.button("Mark As Pending"):
                    sel_task.mark_incomplete()
                    save_all()
                    st.rerun()
        else:
            st.info("No tasks match the selected filters.")
    else:
        st.info(f"{owner.name} has no pets to filter tasks for.")


# ------------------------------------------------------------------ #
#  Tab 2: Health Log                                                   #
# ------------------------------------------------------------------ #
with tabs[1]:
    owner = active_owner()
    st.subheader(f"Health Log — {owner.name}'s Pets")
    st.caption("Track vaccinations, vet visits, medications, and other health events.")

    if not owner.pets:
        st.info(f"Add at least one pet for {owner.name} first.")
    else:
        pet_lookup_h = {p.name: p for p in owner.pets}

        with st.form("add_health_record_form", clear_on_submit=True):
            h_pet = st.selectbox("Select Pet", list(pet_lookup_h.keys()), key="health_pet_select")
            h_type = st.selectbox("Record Type", ["vaccination", "vet visit", "medication", "surgery", "checkup", "other"])
            h_desc = st.text_input("Description", placeholder="Rabies vaccine, annual checkup...")
            h_date = st.date_input("Date", value=date.today())
            h_notes = st.text_area("Notes (optional)", height=60)
            add_h_btn = st.form_submit_button("Add Health Record")

        if add_h_btn:
            clean = h_desc.strip()
            if not clean:
                st.error("Please enter a description.")
            else:
                try:
                    pet_lookup_h[h_pet].add_health_record(HealthRecord(
                        record_type=h_type,
                        description=clean,
                        record_date=h_date,
                        notes=h_notes.strip(),
                    ))
                    st.success(f"Health record added for {h_pet}.")
                    save_all()
                except Exception as exc:
                    st.error(str(exc))

        st.divider()
        view_pet_name = st.selectbox("View Records For", list(pet_lookup_h.keys()), key="health_view_select")
        records = pet_lookup_h[view_pet_name].get_health_records()

        if records:
            st.write(f"Health History for {owner.name}'s {view_pet_name} ({len(records)} record(s))")
            st.table([{
                "Date": r.record_date.isoformat(),
                "Type": r.record_type.capitalize(),
                "Description": r.description,
                "Notes": r.notes or "-",
            } for r in records])
        else:
            st.info(f"No health records yet for {view_pet_name}.")


# ------------------------------------------------------------------ #
#  Tab 3: Build Schedule                                               #
# ------------------------------------------------------------------ #
with tabs[2]:
    owner = active_owner()
    st.subheader(f"Build Schedule — {owner.name}")
    st.caption("Generate today's schedule from this owner's pet tasks using priority and time constraints.")

    slot_duration = st.number_input("Slot Duration to Find (Minutes)", min_value=1, max_value=240, value=30)
    slot_pet_options = ["All Pets"] + [p.name for p in owner.pets]
    slot_pet_choice = st.selectbox("Find Slot For", slot_pet_options, key="slot_pet_choice")

    if st.button("Generate Schedule"):
        if not owner.pets:
            st.warning(f"{owner.name} has no pets yet.")
        else:
            scheduler = Scheduler(owner=owner)
            schedule = scheduler.get_todays_schedule()

            if not schedule:
                st.info("No tasks scheduled for today.")
            else:
                st.write("Today's Sorted Schedule")
                st.table([{
                    "Time": t.time,
                    "Description": t.description,
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority.capitalize(),
                    "Frequency": t.frequency,
                    "Due Date": t.due_date.isoformat(),
                    "Status": "Done" if t.completed else "Pending",
                } for t in schedule])

            daily_plan = scheduler.build_daily_plan()
            if daily_plan:
                st.write("Recommended Daily Plan")
                st.table([{
                    "Time": item["time"],
                    "Description": item["description"],
                    "Priority": item["priority"].capitalize(),
                    "Duration (min)": item["duration_minutes"],
                    "Reason": item["reason"],
                } for item in daily_plan])
            else:
                st.info("No tasks fit the current time budget.")

            warnings = scheduler.detect_conflicts()
            if warnings:
                st.warning("Schedule conflicts found:")
                for w in warnings:
                    st.warning(w)
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
                file_name=f"pawpal_{owner.name}_{date.today().isoformat()}.txt",
                mime="text/plain",
            )


# ------------------------------------------------------------------ #
#  Tab 4: AI Advisor                                                   #
# ------------------------------------------------------------------ #
with tabs[3]:
    owner = active_owner()
    st.subheader(f"AI Advisor — {owner.name}")
    st.caption(
        "Ask the AI to review this owner's pet schedule and suggest improvements. "
        "Advice includes a confidence score and a guardrail flag."
    )

    user_question = st.text_area(
        "Your Question (required)",
        placeholder="Example: Is my dog getting enough exercise? Are any tasks missing?",
        height=80,
        key="ai_question_input",
    )

    if st.button("Get AI Advice"):
        if not owner.pets:
            st.warning(f"Add at least one pet for {owner.name} before asking for advice.")
        elif not user_question.strip():
            st.warning("Please enter something in the box!")
        else:
            with st.spinner("Asking Groq for care advice..."):
                try:
                    result: AdvisorResult = get_care_advice(
                        owner_data=owner.to_dict(),
                        user_question=user_question.strip(),
                    )
                except ValueError as exc:
                    st.error(f"Could not reach the AI advisor: {exc}")
                    result = None
                except Exception as exc:
                    st.error(f"Something went wrong: {exc}")
                    result = None

            if result is not None:
                st.session_state.advice_history.insert(0, {
                    "owner": owner.name,
                    "timestamp": date.today().isoformat(),
                    "question": user_question.strip(),
                    "result": result,
                })
                st.session_state.advice_history = st.session_state.advice_history[:3]

                col_conf, col_flag = st.columns(2)
                with col_conf:
                    st.metric("Confidence", f"{int(result.confidence * 100)}%")
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
            label = (
                f"Run {i + 1} ({entry['timestamp']}) "
                f"[{entry.get('owner', '?')}] "
                f"— {int(r.confidence * 100)}% confidence — {r.flag}"
            )
            with st.expander(label, expanded=(i == 0)):
                st.caption(f"Question: {entry['question']}")
                st.markdown(f"**Summary:** {r.summary}")
                for j, s in enumerate(r.suggestions, 1):
                    st.markdown(f"{j}. {s}")

    st.divider()
    st.markdown(
        "**How it works:** The AI Advisor sends the selected owner's pet schedule to a "
        "Groq-hosted LLM, which identifies care gaps and returns structured suggestions "
        "with a self-rated confidence score. A guardrail layer validates the response "
        "format and flags unsafe or incomplete advice before it reaches you."
    )
