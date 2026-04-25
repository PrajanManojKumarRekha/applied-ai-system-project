# PawPal+ Reflection

## How This Project Grew

PawPal+ started simple. I wanted a tool that could help someone keep track of pet care tasks without losing things in a notebook or a phone note. So I built a scheduling assistant with four core classes: Owner, Pet, Task, and Scheduler. The scheduler handled sorting by time, prioritizing by urgency, detecting when two tasks conflicted, and suggesting the next open slot in the day. Everything was deterministic. Same input, same output, every time.

That worked well for what it was, but it could only tell you what tasks you had, not whether those tasks were actually good for your pets. A dog owner could schedule one five-minute walk a week and the app would just show it as a task. There was no layer that could say "this is not enough for a high-energy breed."

That gap pushed me toward adding an AI advisor. My first idea was simple: pass the schedule to a language model, ask for feedback. But I kept running into the same problem when testing that approach. The advice was vague. "Make sure your pet gets enough exercise" is not useful if you already know that and want to know whether 30 minutes is enough for a Border Collie specifically. The model needed to know what good care actually looks like, not just guess based on training data.

That is when I switched to a retrieval-augmented approach. I built a local knowledge base of 20 curated pet care documents covering exercise needs, vaccination schedules, feeding guidelines, dental care, and scheduling best practices, all tagged by species. Before calling the LLM, the system identifies which species the owner has, retrieves the most relevant knowledge chunks from a ChromaDB vector store, and injects them into the prompt. The model then has actual facts to reason from rather than generic impressions.

The difference in advice quality was noticeable right away. Questions about dogs came back with breed-appropriate suggestions referencing exercise durations. Cat questions surfaced litter hygiene and vaccination reminders. The grounding was working.

## What I Used AI For During Development

I used AI assistance at several points, but not to write code wholesale. The most useful sessions were the ones where I described a problem and asked what could go wrong.

When I was designing the guardrail, I described the pipeline and asked what failure modes I should protect against. That conversation surfaced the full list: missing JSON keys, confidence values outside 0 to 1, invalid flag strings, and the model sometimes wrapping the JSON in markdown fences even when told not to. Every one of those became a real test case. Without that conversation I probably would have caught two or three of them and been surprised by the rest in production.

I also used it to think through the knowledge base design. What topics matter most across the species I was targeting? What is specific enough to be useful but generic enough to not require per-breed data? That back and forth helped me land on the 20-document structure that covers the important cases without becoming a veterinary database.

### One Suggestion That Helped

The best suggestion was about what to do when the guardrail fires. My instinct was to raise a `ValueError` and catch it in the Streamlit layer with a generic error message. The suggestion was to instead return a structured `AdvisorResult` with `confidence=0.0` and `flag="incomplete_data"` containing a plain-English explanation.

That turned out to be the right call for a few reasons. The UI stays consistent because the result shape never changes regardless of what the model does. The owner gets a clear message instead of a stack trace. And the guardrail behavior is directly testable because you can write a test that checks the exact confidence and flag values on a bad response, which I did. Raising an exception would have made that test much messier.

### One Suggestion That Did Not Work

The suggestion I did not follow was to build a multi-turn conversation loop where the model asks clarifying questions before giving advice, things like "does your dog have any health conditions?" or "how long has this task been in the schedule?"

It sounded like it would produce more personalized advice. But it was wrong for this project for a few reasons. The app already has a care notes field per pet where the owner can put exactly that kind of context before asking. A conversation loop would require persisting the chat history across Streamlit reruns, which introduces its own session state bugs and makes the system significantly harder to test. And the retrieval step already compensates for sparse data by pulling in species-appropriate best practices. The single-turn design with strong retrieval produces specific, grounded advice without the added complexity.

## Testing and What I Learned

I wrote 32 automated tests covering the scheduler logic, the AI Advisor pipeline, and the RAG layer separately. The tests mock the Groq client and the vector store so they run without an API key and produce consistent results regardless of what is stored locally.

The guardrail tests ended up being the most important ones. They confirmed that a model returning plain text, or JSON missing required keys, or a confidence value of 1.5 all produce a predictable safe fallback rather than an exception. That is the behavior that matters most in production.

One thing I learned while writing the tests is that you have to patch `ai_advisor.retrieve` directly, not let it hit the real ChromaDB. The first few test runs were flaky because the vector store on disk had different content depending on what I had done locally. Once I patched the retrieve function the tests became fully deterministic.

I also ran a manual end-to-end test with a real Groq API key and real pet data. The automated suite covers the shape of the system but not the quality of the advice, and that can only be evaluated by actually reading the output.

## Limitations and Ethics

The advisor only knows what is in the data. It cannot see whether the owner is actually doing the tasks, whether the pet is stressed, or whether a condition has gotten worse since the last vet visit. A schedule that looks fine on paper might be missing the most important thing.

The confidence score is self-reported by the model, which means a high score reflects how certain the model was, not whether the advice is actually correct. I kept it in because showing uncertainty is better than hiding it, but it is not a quality guarantee.

The knowledge base covers common domestic species reasonably well. Exotic animals, senior pets, and pets with chronic conditions will get generic advice because those topics are not in the 20 documents. The system is honest about this because the retrieved chunks are visible in the UI, so the owner can see when the knowledge that was retrieved does not really apply.

The biggest misuse risk is an owner treating AI advice as a substitute for a vet. The guardrail flag system flags cases where a vet visit appears to be missing, the system prompt explicitly prohibits medication recommendations, and the confidence score is visible. But none of that stops someone who is determined to avoid the vet. I added the "Missing Vet Visit" flag specifically to surface that case rather than let the model silently produce wellness advice when the real issue is that the pet has not been seen by a professional.

## What This Taught Me

The thing that surprised me most was that overly complete data produced worse advice than sparse data with real gaps. When every task was filled in with high priority and no conflicts existed, the model tended to say everything looked fine and produce vague suggestions. When there were actual gaps or conflicts, the suggestions were specific and actionable. The retrieval layer helped a lot here because even when the schedule data was thin, the retrieved knowledge gave the model enough context to say what was typically missing for that species.

The bigger lesson is about where reliability comes from. I went into this thinking reliability meant making the model give better answers. What I actually built was a system where bad answers are caught and handled before they reach the user. The guardrail, the confidence score, and the retrieved knowledge panel together give the owner what they need to decide how much to trust the output. That is more useful than trying to make the model always right, because no amount of prompt engineering makes that true.
