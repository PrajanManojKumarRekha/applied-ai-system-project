# PawPal+ Applied AI System

## Original Project

This project started as **PawPal+**, a pet care scheduling assistant built during Modules 1 through 3 of the CodePath Applied AI course. The original goal was to help a busy pet owner stay on top of daily care tasks by tracking pets and tasks, building a prioritized daily schedule, detecting conflicts, and suggesting the next open time slot. The system was built in Python with a Streamlit web UI and a pytest test suite covering 25 cases.

## What Is New in Module 4

Module 4 adds a full agentic AI workflow powered by the Groq API, plus several production-quality features that make the app genuinely useful day to day.

**AI Advisor (agentic workflow)**
- Analyzes the owner's entire pet and task data in a single context pass
- Calls a Groq-hosted LLM to produce structured care advice with concrete suggestions
- Rates its own confidence on a 0.0 to 1.0 scale
- Applies a guardrail layer that validates the response format before showing results
- Flags potentially unsafe situations such as a missing vet visit or an overloaded schedule
- Shows the raw JSON response in an expandable panel for transparency
- Keeps the last 3 advice runs in session so you can compare results

**Pet Health Log**
- Tracks vaccinations, vet visits, medications, surgeries, and checkups per pet
- Records are stored in the same data.json file alongside tasks and are shown sorted by date

**Task Completion Streak Tracker**
- Each pet earns a consecutive-day streak when all its daily tasks are completed
- Streaks are displayed in the sidebar with fire and sparkle indicators at 3 and 7 days

**Sidebar Stats Dashboard**
- Live metrics: total pets, total tasks, completed count, pending count, completion rate, time used vs daily budget
- Per-pet streak display updates without a page refresh

**Schedule Export**
- Generates a plain-text version of today's schedule and recommended plan
- Provides a download button to save it as a dated .txt file

## Architecture Overview

```
User (Browser)
     |
     v
Streamlit App (app.py)  [wide layout with sidebar stats]
     |
     |-- Sidebar
     |       |
     |       v
     |   Owner.completion_rate()
     |   Owner.total_minutes_completed()
     |   Pet.streak_days
     |
     |-- Tab 1: Pets and Tasks
     |       |
     |       v
     |   pawpal_system.py
     |   Owner / Pet / Task / Scheduler
     |   data.json (persistence)
     |
     |-- Tab 2: Health Log
     |       |
     |       v
     |   Pet.health_records (List[HealthRecord])
     |   HealthRecord: type, description, date, notes
     |   data.json (persistence)
     |
     |-- Tab 3: Build Schedule
     |       |
     |       v
     |   Scheduler.build_daily_plan()
     |   Scheduler.detect_conflicts()
     |   Scheduler.next_available_slot()
     |   Scheduler.export_schedule_text()
     |
     |-- Tab 4: AI Advisor
             |
             v
         ai_advisor.py
         _build_context()       <-- converts owner dict to plain text
             |
             v
         Groq API (llama-3.3-70b-versatile)
             |
             v
         _parse_response()      <-- guardrail: validates JSON keys,
                                    confidence range, flag values
             v
         AdvisorResult
         summary / suggestions / confidence / flag / is_safe
             |
             v
         Session advice_history (last 3 runs)
```

Data flows from the owner's saved state into a plain-text context summary, which goes to the LLM as the user message. The model returns a JSON object. The guardrail validates required keys, confidence range, and flag value. Only a clean result reaches the display layer. If validation fails, a safe fallback result is returned instead of crashing.

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- A Groq API key (free at console.groq.com, only needed for the AI Advisor tab)

### Install

```bash
git clone https://github.com/PrajanManojKumarRekha/applied-ai-system-project.git
cd applied-ai-system-project
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configure your API key

Open the `.env` file in the project root and replace the placeholder:

```
GROQ_API_KEY=your_groq_api_key_here
```

The app loads this automatically via python-dotenv. You never paste it into the UI.

### Run the App

```bash
streamlit run app.py
```

Open the URL printed in the terminal (usually http://localhost:8501).

### Run the Tests

```bash
python -m pytest
```

All 25 tests pass. The AI Advisor tests use a mocked Groq client so no API key is needed to run them.

## Sample Interactions

### Example 1: Dog with a consistent schedule

Owner: Jordan, 120 min/day  
Pet: Mochi (dog) with morning walk, lunch feed, evening enrichment

Optional question: "Is Mochi getting enough mental stimulation?"

AI Advisor output:
```
Confidence: 87%
Flag: All Clear

Summary: Mochi has a solid daily routine but mental enrichment appears only weekly.

Suggestions:
1. Add a short puzzle feeder session 3 times a week to increase cognitive engagement.
2. Consider a second shorter walk in the evening to break up long gaps.
3. Rotate enrichment activities so Mochi does not get bored with the same weekly task.
```

### Example 2: Cat with a time conflict and no vet task

Owner: Alex, 60 min/day  
Pet: Luna (cat) with two tasks at 14:00 and no health records

AI Advisor output:
```
Confidence: 79%
Flag: Missing Vet Visit

Summary: Luna's schedule has a time conflict at 14:00 and no vet checkup task.

Suggestions:
1. Shift dental care to 15:00 to resolve the grooming conflict.
2. Add a quarterly vet visit reminder task to keep health records current.
3. Reduce grooming to every two weeks if daily time is limited to 60 minutes.
```

### Example 3: Guardrail on a malformed model response

If the model returns plain text instead of JSON, the guardrail intercepts it:

```
Confidence: 0%
Flag: Incomplete Data

Summary: The AI advisor could not produce a valid response. Please try again.

Suggestions:
1. Check that your pets and tasks are set up correctly before asking for advice.
```

## Design Decisions

**Why Groq instead of OpenAI or Anthropic?**  
Groq provides fast inference for open-weight models at no cost for moderate usage. The llama-3.3-70b-versatile model handles the structured JSON task well. The model is a parameter in `get_care_advice`, so swapping it requires one line of code.

**Why a structured JSON response?**  
Asking the model to return raw text makes the output hard to test or display reliably. By specifying a schema in the system prompt and validating it in `_parse_response`, the advisor is both testable and safe. If the model returns anything outside the schema, the guardrail returns a safe fallback rather than showing garbage to the user.

**Why confidence scoring?**  
Confidence gives the owner a quick signal about how much weight to put on the advice. A low score usually means the data was too sparse for the model to reason well. This makes the AI's uncertainty visible rather than hiding it.

**Why a single-turn workflow?**  
The owner's data is already fully captured in the context, so a multi-turn loop would add complexity without meaningful benefit. The architecture is modular so a multi-step loop could be added in a future version.

**Why store health records in data.json alongside tasks?**  
It keeps persistence simple with no external database. The HealthRecord dataclass uses the same to_dict / from_dict pattern as Task, so it slots into the existing serialization without new dependencies.

## Testing Summary

25 tests total, all passing.

- 13 tests cover the original scheduler: time sorting, priority filtering, conflict detection, daily plan construction, next available slot, persistence round-trip, and edge cases.
- 12 tests cover the AI Advisor module: context building, JSON parsing, guardrail behavior on bad responses, missing API key validation, the is_safe property, and end-to-end advice flow with a mocked Groq client.

The guardrail test specifically confirms that a model returning plain text instead of JSON produces a safe fallback AdvisorResult with confidence 0.0 and flag "incomplete_data" rather than raising an exception.

One limitation: tests mock the Groq client, so real model behavior is not exercised in CI. A manual integration test was run with a live key to confirm end-to-end behavior before submission.

## Reflection

See [reflection.md](reflection.md) for a full reflection covering AI collaboration, limitations, ethics, and what this project taught about building reliable AI systems.

## Demo Screenshots

![Pets and Tasks tab](image.png)
![Build Schedule tab](image-1.png)
![AI Advisor tab](image-2.png)
