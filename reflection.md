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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
