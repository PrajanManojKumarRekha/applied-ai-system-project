# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

- Add and manage multiple pets under one owner profile.
- Add pet care tasks with time, frequency, due date, and completion state.
- Sort tasks by time so the schedule is easy to follow.
- Filter tasks by pet name and by completion status.
- Auto create the next task when a daily or weekly task is completed.
- Detect exact time conflicts and show warning messages.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

The scheduler now includes a few small algorithmic improvements to better support a busy pet owner:

- Sorting by time: tasks are sorted using the `HH:MM` time field so the day plan is in order.
- Filtering by pet and status: tasks can be filtered by pet name and completion state.
- Recurring task automation: when a daily or weekly task is completed, a new future task is created automatically.
- Conflict detection: the scheduler returns warning messages when two pending tasks share the same date and time.

## 📸 Demo

<a href="/course_images/ai110/pawpal_app.png" target="_blank"><img src='/course_images/ai110/pawpal_app.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

## Testing PawPal+

Run the test suite with:

```bash
python -m pytest
```

The tests currently cover:

- task completion state changes
- adding tasks to pets
- time based sorting correctness
- filtering by pet and completion status
- recurring daily task creation for the next day
- exact time conflict warnings
- pets with no tasks

Confidence Level: 4/5 stars

The scheduler is reliable for the tested paths and common edge cases. The next area to expand is overlap checking for tasks with durations.
