# PawPal+ Applied AI System

## Original Project

This project started as **PawPal+**, a pet care scheduling assistant built during Modules 1 through 3 of the CodePath Applied AI course. The original goal was to help a busy pet owner stay on top of daily care tasks by tracking pets and tasks, building a prioritized daily schedule, detecting conflicts, and suggesting the next open time slot. The system was built in Python with a Streamlit web UI and a pytest test suite.

## What Is New in Module 4

Module 4 adds a full agentic AI workflow powered by the Claude API. The new **AI Advisor** feature:

- Analyzes the owner's entire pet and task data in a single context pass
- Calls Claude to produce structured care advice with concrete suggestions
- Rates its own confidence on a 0.0 to 1.0 scale
- Applies a guardrail layer that validates the response format before showing results to the user
- Flags potentially unsafe situations such as a missing vet visit or an overloaded schedule

This is not an isolated demo. The advisor reads the same owner and task data that the rest of the app manages, so advice is always based on what is actually scheduled.

## Architecture Overview

```
User (Browser)
     |
     v
Streamlit App (app.py)
     |
     |-- Tab 1: Pets and Tasks
     |       |
     |       v
     |   pawpal_system.py
     |   Owner / Pet / Task / Scheduler
     |   data.json (persistence)
     |
     |-- Tab 2: Build Schedule
     |       |
     |       v
     |   Scheduler.build_daily_plan()
     |   Scheduler.detect_conflicts()
     |   Scheduler.next_available_slot()
     |
     |-- Tab 3: AI Advisor
             |
             v
         ai_advisor.py
         _build_context()       <-- converts owner dict to plain text
             |
             v
         Claude API (claude-haiku-4-5)
             |
             v
         _parse_response()      <-- guardrail: validates JSON keys,
         |                          confidence range, flag values
             v
         AdvisorResult
         summary / suggestions / confidence / flag / is_safe
```

Data flows from the owner's saved state into a plain-text context summary, which goes to Claude as the user message. Claude returns a JSON object. The guardrail function checks that the object has all required keys, that confidence is between 0 and 1, and that the flag is a known value. Only then does the result reach the Streamlit display layer.

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- An Anthropic API key (only needed for the AI Advisor tab)

### Install

```bash
git clone https://github.com/PrajanManojKumarRekha/applied-ai-system-project.git
cd applied-ai-system-project
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the App

```bash
streamlit run app.py
```

Open the URL printed in the terminal (usually http://localhost:8501).

### Run the Tests

```bash
python -m pytest
```

All 25 tests should pass. The AI Advisor tests use a mocked Anthropic client so no API key is required.

### Optional Environment Variable

If you want the API key pre-filled in the UI, set it before running:

```bash
export ANTHROPIC_API_KEY=your_key_here   # Windows: set ANTHROPIC_API_KEY=your_key_here
streamlit run app.py
```

## Sample Interactions

### Example 1: Dog with a well-structured schedule

Input (owner data in the AI Advisor tab):

```
Owner: Jordan, 120 min/day
Pet: Mochi (dog)
  - [pending] Morning walk at 08:00 (30 min, high, daily)
  - [pending] Lunch feed at 12:00 (15 min, medium, daily)
  - [pending] Evening enrichment at 18:00 (20 min, medium, weekly)
```

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

### Example 2: Cat with no vet task and an overloaded afternoon

Input:

```
Owner: Alex, 60 min/day
Pet: Luna (cat)
  - [pending] Breakfast at 07:00 (10 min, high, daily)
  - [pending] Grooming at 14:00 (30 min, medium, weekly)
  - [pending] Dental care at 14:00 (20 min, low, weekly)
  - [pending] Dinner at 18:00 (10 min, high, daily)
```

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

### Example 3: Guardrail on incomplete data

Input: Owner with no pets added yet.

AI Advisor output:

```
Confidence: 0%
Flag: Incomplete Data

Summary: The AI advisor could not produce a valid response. Please try again.

Suggestions:
1. Check that your pets and tasks are set up correctly before asking for advice.
```

## Design Decisions

**Why a structured JSON response from Claude?**
Asking Claude to return raw text would make it difficult to display advice reliably or to test. By specifying a fixed schema in the system prompt and validating it in `_parse_response`, the advisor is both testable and safe. If the model returns anything outside the schema, the guardrail catches it and returns a safe fallback result instead of showing garbage to the user.

**Why confidence scoring?**
Confidence gives the owner a quick signal about how much to trust the advice. A low score usually means the data was sparse. A high score means the model had enough context to reason well. This is a form of self-critique that makes the AI's uncertainty visible rather than hiding it.

**Why claude-haiku and not a larger model?**
The context is short (a few dozen lines of text), and the output is tightly constrained (a small JSON object). Haiku handles this well at lower cost and lower latency. The model choice is a parameter so it can be overridden easily.

**Tradeoff: single-turn vs. multi-turn agentic loop**
A more advanced design would use a multi-turn loop where the model can ask follow-up questions or look up external resources. This project uses a single-turn design because the owner's data is already fully captured in the context, and a loop would add complexity without meaningful benefit for this scope. The architecture is set up so a multi-turn loop could be added later.

## Testing Summary

25 tests total, all passing.

- 13 tests cover the original scheduler (sorting, filtering, conflict detection, persistence, edge cases).
- 12 tests cover the AI Advisor module (context building, JSON parsing, guardrail behavior, mock API calls, confidence validation, flag values, user question passthrough).

The guardrail test specifically verifies that a model returning plain text instead of JSON results in a safe fallback AdvisorResult with confidence 0.0 and flag "incomplete_data" rather than crashing the app.

One limitation: tests mock the Anthropic client, so real model behavior is not exercised in CI. A manual integration test was run with a live key to confirm end-to-end behavior before submission.

## Reflection

See [reflection.md](reflection.md) for a full reflection covering AI collaboration, limitations, ethics, and what this project taught about building reliable AI systems.

## Demo Screenshots

![Pets and Tasks tab](image.png)
![Build Schedule tab](image-1.png)
![AI Advisor tab](image-2.png)
