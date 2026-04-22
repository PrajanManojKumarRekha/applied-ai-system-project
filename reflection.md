# PawPal+ Project Reflection (Module 4)

## 1. System Design

### Original Design (Modules 1 to 3)

PawPal+ started as a scheduling assistant for pet owners. The core idea was simple: help someone keep track of care tasks, build a prioritized daily plan, and avoid conflicts.

I designed four main classes: Owner, Pet, Task, and Scheduler. Owner holds the time budget and preferences. Pet holds care notes and a task list. Task holds the description, time, priority, frequency, and duration. Scheduler handles sorting, filtering, conflict detection, time slot search, and daily plan building.

The original system was entirely rule-based. It scored tasks by priority and owner preferences, sorted them by time, and produced an explainable plan. No external AI model was involved.

### Module 4 Extension

Module 4 asked me to add a substantial AI feature. I chose to build an agentic workflow that sends the owner's full schedule context to Claude and gets structured care advice back. This is integrated as a third tab in the Streamlit app rather than a standalone demo, so it operates on the same data the owner is already managing.

The new component is ai_advisor.py. It contains a context builder that converts the Owner dictionary into plain text, a call to the Claude API, a guardrail function that validates the response format, and a typed AdvisorResult dataclass.

### Design Changes from Original Plan

I originally considered a multi-turn loop where Claude could ask clarifying questions. I dropped this because the owner's data is already fully captured in context, and adding a loop would increase complexity without improving advice quality for this scope. The single-turn design is easier to test, easier to reason about, and still produces genuinely useful output.

---

## 2. Scheduling Logic and New AI Layer

### How the Two Systems Work Together

The original scheduler is deterministic. It applies fixed rules and produces the same output every time for the same input. The AI Advisor layer is probabilistic. It interprets patterns in the schedule and generates natural language suggestions that the deterministic scheduler cannot produce.

Neither replaces the other. The scheduler is better for building the actual plan. The AI Advisor is better for spotting care gaps, imbalances, and missing items that are not captured in the data.

### Tradeoffs

The main tradeoff is trust. Deterministic scheduling output is fully explainable and verifiable. AI-generated advice is plausible but could be wrong. I addressed this with three design choices. First, the system prompt restricts Claude from recommending medications or specific dosages. Second, the response schema is validated before results reach the UI. Third, a confidence score is shown so the owner can calibrate how much weight to give the advice.

---

## 3. AI Collaboration During Development

### How I Used AI

I used Claude Code to help design the system prompt for the advisor and to think through the guardrail validation logic. I also used it to review the structure of the test suite and suggest edge cases I had not thought of.

The most useful interaction was when I asked for help thinking through what could go wrong with the model response. Claude suggested testing for markdown fences around JSON, out-of-range confidence values, and missing required keys. All three became real test cases that the guardrail now handles.

### Helpful Suggestion

The most helpful suggestion was to return a safe fallback AdvisorResult instead of raising an exception when the guardrail fails. My first instinct was to let the exception propagate and catch it in the Streamlit layer. Claude pointed out that catching a ValueError in the UI creates a worse user experience than returning a graceful result with a clear explanation. The fallback result approach also made the guardrail behavior directly testable, which the exception approach would not have been.

### Flawed Suggestion

Claude suggested I use a multi-turn conversation loop where the model could ask the user clarifying questions before generating advice. The idea was that the model could ask "does your dog have any allergies?" and then refine its suggestions based on the answer. This sounded appealing but was wrong for this project. PawPal+ already captures care notes per pet, so the owner can put that information in the data before asking for advice. Adding a multi-turn loop would require managing conversation history across Streamlit reruns, which introduces significant complexity and session state bugs. I kept the single-turn design and the advice quality did not suffer.

---

## 4. Testing and Verification

### What I Tested

I wrote 25 automated tests. The first 13 cover the original scheduler and are unchanged from Module 3. The new 12 tests cover:

- Context building with and without pets
- JSON parsing for valid responses, markdown-wrapped responses, missing keys, and out-of-range confidence
- Guardrail behavior when the model returns plain text instead of JSON
- Missing API key validation
- The is_safe property on AdvisorResult
- End-to-end advice generation with a mocked Anthropic client
- User question passthrough to the API call

### Results

All 25 tests pass. The guardrail tests are the most important because they confirm that a bad model response does not crash the app or show confusing output to the user.

One thing I learned is that mocking the Anthropic client is straightforward but does not catch prompt engineering errors. I found one case during manual testing where the model returned valid JSON but gave advice that was too generic to be useful. The fix was to tighten the system prompt to require concrete, specific suggestions rather than abstract guidance.

### Confidence

My confidence level is 4 out of 5. The tested paths are solid. The gap is in real-world prompt robustness. Different model versions or unusual pet data could produce edge cases the mock tests would not catch.

---

## 5. Limitations, Bias, and Ethics

### Limitations

The AI Advisor only knows what is in the schedule. It cannot observe the pet's actual behavior, health, or environment. This means it might suggest adding more tasks for a pet that is already stressed, or miss that a "daily walk" listed in the data is actually not happening.

The system prompt tells Claude not to recommend medications, but it has no way to verify whether a task labeled "give meds" is safe or appropriate. The advice is general wellness guidance, not veterinary care.

The confidence score is self-reported by the model. A high confidence score does not mean the advice is correct. It means the model felt certain, which is not the same thing.

### Potential for Misuse

A pet owner who trusts AI advice uncritically might delay a vet visit because the advisor said the schedule looks good. To reduce this risk, the flag system surfaces cases where the data suggests a vet appointment is missing. The UI also shows a note explaining that the advisor gives general guidance and is not a substitute for professional veterinary care.

### What Surprised Me

I expected the model to struggle with sparse data. What actually surprised me was that it struggled more with overly structured data. When every task was perfectly filled in with high priority and short duration, the model tended to say everything looked fine and give weak suggestions. When there were actual gaps or conflicts in the data, the suggestions were much more specific and useful. This suggests the advisor works best as a second opinion when the schedule has real problems, not as a final check on an already polished plan.

### Key Takeaway

Building this project taught me that reliability in AI systems is not just about whether the model gives good answers. It is about whether bad answers are caught before they reach the user. The guardrail and confidence score together give the owner the information they need to decide how much to trust the output. That is more useful than trying to make the model always right.
