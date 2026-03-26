# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

From the README scenario, PawPal+ should help a busy owner keep up with pet care tasks each day.

The three core user actions are:
- Add and update pet and owner information.
- Add and edit care tasks like walks, feeding, meds, enrichment, and grooming.
- Generate and view a daily plan that explains why tasks were chosen.

To support these actions, I drafted four main classes.

Owner
- Attributes: name, daily time available, preferred task types.
- Methods: add_pet(), add_task(), set_time_limit().

Pet
- Attributes: name, species, care notes.
- Methods: update_notes().

Task
- Attributes: title, category, duration_minutes, priority, required.
- Methods: mark_done(), fits_in(remaining_minutes).

Scheduler
- Attributes: time_limit_minutes.
- Methods: score_task(task), build_plan(owner), explain_plan(plan).

I also added a PlanItem object in the code skeleton to hold one scheduled item with start time, end time, and reason. This keeps the plan output clean.

**b. Design changes**

I reviewed my skeleton and noticed one missing relationship. The plan output needed its own structure, so I added PlanItem to connect a selected task with a time range and reason text.

I also kept scoring in Scheduler and did not split it into too many small classes yet. This avoids extra complexity at this stage and keeps the starter code easy to follow.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

My scheduler focuses on time, completion status, recurring frequency, and exact time conflicts. Time matters because the owner needs a clear order for the day. Completion status matters so the app can separate what is done and what is still pending. Frequency matters because daily and weekly tasks should keep repeating. Conflicts matter because two tasks at the same time can create stress for the owner.

I treated time ordering and completion status as the most important constraints first. Those two parts make the app useful right away. Then I added recurrence and conflict warnings to improve planning quality.

**b. Tradeoffs**

One tradeoff in my scheduler is conflict detection. Right now it checks only exact date and time matches, not overlapping durations.

This is reasonable for this project stage because it keeps the logic simple, fast to run, and easy to explain. It still catches common schedule issues, and I can add overlap checks later if needed.

---

## 3. AI Collaboration

**a. How you used AI**

I used Copilot most for planning and for fast code refinement. It helped me brainstorm class design, add scheduler methods, and draft tests. It was also useful for small refactors when I wanted cleaner method structure.

The most helpful prompts were specific ones like asking how to sort HH:MM times with a key function, how to use timedelta for recurring tasks, and how to design lightweight conflict detection.

**b. Judgment and verification**

One time I rejected a more complex conflict detection idea that tried to model duration overlaps and advanced scheduling rules. I kept a simpler exact time match strategy because it fit the project scope better.

I verified each change by running python main.py and python -m pytest, then checking if the outputs matched expected behavior.

---

## 4. Testing and Verification

**a. What you tested**

I tested task completion state changes, adding tasks to pets, sorting order, filtering by pet and status, recurring task creation for daily tasks, conflict warnings for same time tasks, and the edge case of a pet with no tasks.

These tests are important because they cover both the main workflow and edge cases that can break user trust if not handled well.

**b. Confidence**

My confidence level is 4 out of 5 based on passing automated tests and manual demo runs.

If I had more time, I would test overlapping duration conflicts, invalid time formats from user input, and very large numbers of tasks across many pets.

---

## 5. Reflection

**a. What went well**

I am most satisfied with how the scheduler evolved from a simple list sorter into a smarter planner with filtering, recurrence, and conflict warnings.

**b. What you would improve**

In another iteration, I would redesign conflict detection to support overlapping time windows instead of exact match only. I would also improve the Streamlit workflow for marking tasks complete directly in the UI.

**c. Key takeaway**

My key takeaway is that AI works best when I stay the lead architect. Copilot can speed up writing and testing, but I still need to choose the scope, keep the design simple, and verify behavior with clear tests.

---

## 6. Prompt Comparison

I compared one complex prompt about weekly rescheduling logic across two model responses, GPT and Gemini.

The GPT response was more modular in structure and easier to plug into my existing class methods. It suggested clear helper methods and cleaner control flow for recurrence handling.

The Gemini response was also useful, but it focused more on broad explanation and less on direct method level integration.

I used the more modular style because it was easier to test with pytest and easier to maintain.

Using separate chat sessions for design, implementation, and testing helped me stay organized. It reduced context mixing and made each decision easier to verify.
