"""
PawPal+ RAG Knowledge Base

Builds and queries a persistent ChromaDB vector store of pet care knowledge.
The store lives in ./chroma_db/ and is created once on first use.

The knowledge documents cover:
  - Species-specific exercise and enrichment needs
  - Vaccination and vet visit schedules by species
  - Common health flags and warning signs
  - Nutrition and feeding guidelines
  - Task scheduling best practices

retrieve() is the public API used by the AI Advisor agent.
"""

import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

logger = logging.getLogger(__name__)

_CHROMA_DIR = "chroma_db"
_COLLECTION = "pet_care_knowledge"

_KNOWLEDGE_DOCS = [
    # ---- Dogs --------------------------------------------------------
    {
        "id": "dog_exercise_daily",
        "text": (
            "Dogs require daily physical exercise. Most adult dogs need 30 to 60 minutes of "
            "aerobic activity per day depending on breed. High-energy breeds like Border Collies "
            "and Huskies need 90 or more minutes. Lack of exercise leads to destructive behavior, "
            "anxiety, and obesity. Two walks per day is a good baseline for medium-sized dogs."
        ),
        "metadata": {"species": "dog", "topic": "exercise"},
    },
    {
        "id": "dog_mental_enrichment",
        "text": (
            "Dogs need mental enrichment in addition to physical exercise. Puzzle feeders, "
            "nose-work games, training sessions, and rotating toys prevent boredom. "
            "Mental stimulation can tire a dog as effectively as a walk. Aim for at least "
            "one enrichment activity per day for working or intelligent breeds."
        ),
        "metadata": {"species": "dog", "topic": "enrichment"},
    },
    {
        "id": "dog_vaccination_schedule",
        "text": (
            "Core vaccines for dogs include distemper, parvovirus, adenovirus, and rabies. "
            "Puppies need a series starting at 6-8 weeks with boosters every 3-4 weeks until "
            "16 weeks, then a booster at 1 year, then every 1-3 years. Rabies is legally "
            "required in most regions. Annual vet checkups are recommended for adult dogs."
        ),
        "metadata": {"species": "dog", "topic": "vaccination"},
    },
    {
        "id": "dog_dental_care",
        "text": (
            "Dental disease is the most common health issue in dogs over age 3. Daily tooth "
            "brushing is ideal; a weekly dental chew is the minimum. Professional dental "
            "cleaning under anesthesia is typically needed every 1-2 years. Signs of dental "
            "problems include bad breath, difficulty eating, and pawing at the mouth."
        ),
        "metadata": {"species": "dog", "topic": "dental"},
    },
    {
        "id": "dog_feeding_guidelines",
        "text": (
            "Adult dogs should be fed twice a day at consistent times. Puppies under 6 months "
            "need three to four meals. Free feeding leads to overeating and obesity. Portion "
            "size depends on weight and activity level. Fresh water must always be available. "
            "Avoid feeding grapes, raisins, chocolate, onions, and xylitol."
        ),
        "metadata": {"species": "dog", "topic": "nutrition"},
    },
    {
        "id": "dog_grooming",
        "text": (
            "Grooming frequency depends on coat type. Short-coated dogs need brushing once a "
            "week and bathing monthly. Long-coated breeds need daily brushing and bathing every "
            "2-4 weeks. All dogs need nail trimming every 3-4 weeks and ear cleaning monthly. "
            "Matting in long coats can cause skin infections if not addressed."
        ),
        "metadata": {"species": "dog", "topic": "grooming"},
    },
    # ---- Cats --------------------------------------------------------
    {
        "id": "cat_exercise_enrichment",
        "text": (
            "Cats need 15-30 minutes of interactive play per day to maintain healthy weight and "
            "mental wellbeing. Indoor cats are at higher risk of obesity and boredom-related "
            "issues. Feather wands, laser pointers, and puzzle feeders are effective enrichment "
            "tools. Cats are crepuscular so play sessions at dawn and dusk match their natural rhythm."
        ),
        "metadata": {"species": "cat", "topic": "exercise"},
    },
    {
        "id": "cat_vaccination_schedule",
        "text": (
            "Core vaccines for cats include feline herpesvirus, calicivirus, panleukopenia, "
            "and rabies. Kittens receive a series starting at 6-8 weeks with boosters every "
            "3-4 weeks until 16 weeks, then at 1 year. Adults are boosted every 1-3 years "
            "depending on lifestyle. Indoor cats still require core vaccines. Annual vet "
            "checkups are important for early detection of kidney and thyroid disease."
        ),
        "metadata": {"species": "cat", "topic": "vaccination"},
    },
    {
        "id": "cat_litter_hygiene",
        "text": (
            "Litter boxes should be scooped daily and fully cleaned weekly. The rule of thumb "
            "is one litter box per cat plus one extra. A dirty litter box is a leading cause "
            "of house soiling and urinary issues. Place boxes in quiet, accessible locations "
            "away from food bowls. Covered boxes may trap odors that deter some cats."
        ),
        "metadata": {"species": "cat", "topic": "hygiene"},
    },
    {
        "id": "cat_feeding_guidelines",
        "text": (
            "Adult cats should be fed measured meals twice a day to prevent obesity. Kittens "
            "under 6 months need three to four small meals. Wet food supports hydration since "
            "cats have a low thirst drive. Mix of wet and dry is common. Avoid free feeding "
            "dry kibble. Fresh water should always be available; some cats prefer a fountain."
        ),
        "metadata": {"species": "cat", "topic": "nutrition"},
    },
    {
        "id": "cat_dental_care",
        "text": (
            "Dental disease affects 70 percent of cats by age 3. Daily brushing with pet-safe "
            "toothpaste is best. Dental treats and water additives offer partial benefit. "
            "Annual professional dental cleanings under anesthesia are recommended. Signs of "
            "pain include dropping food, drooling, and reduced grooming."
        ),
        "metadata": {"species": "cat", "topic": "dental"},
    },
    # ---- Birds -------------------------------------------------------
    {
        "id": "bird_enrichment",
        "text": (
            "Pet birds require daily out-of-cage time for social interaction and flight exercise. "
            "Parrots and cockatiels need 2-4 hours outside the cage each day. Toys, foraging "
            "puzzles, and rotating perches prevent boredom and feather-destructive behavior. "
            "Social birds should not be left alone for extended periods without enrichment."
        ),
        "metadata": {"species": "bird", "topic": "enrichment"},
    },
    {
        "id": "bird_nutrition",
        "text": (
            "A seed-only diet is nutritionally incomplete for most pet birds. Pellets should "
            "form 60-70 percent of the diet. Fresh vegetables, fruits, and cooked grains "
            "supplement nutrition. Avoid avocado, chocolate, onion, caffeine, and alcohol "
            "which are toxic to birds. Fresh water must be changed daily to prevent bacterial growth."
        ),
        "metadata": {"species": "bird", "topic": "nutrition"},
    },
    {
        "id": "bird_vet_care",
        "text": (
            "Birds hide illness as a survival instinct, so annual vet checkups with an avian "
            "specialist are essential for early detection. Signs that need immediate attention "
            "include fluffed feathers, lethargy, discharge from nostrils, and changes in "
            "droppings. Birds need annual weight monitoring as weight loss is an early illness sign."
        ),
        "metadata": {"species": "bird", "topic": "veterinary"},
    },
    # ---- Rabbits -----------------------------------------------------
    {
        "id": "rabbit_exercise",
        "text": (
            "Rabbits need at least 3 hours of free-roaming exercise per day outside their enclosure. "
            "A space of at least 3x3 meters is recommended for unsupervised play. Lack of exercise "
            "causes obesity and GI stasis. Rabbits are most active at dawn and dusk. "
            "Tunnels, cardboard boxes, and digging boxes provide natural enrichment."
        ),
        "metadata": {"species": "rabbit", "topic": "exercise"},
    },
    {
        "id": "rabbit_diet",
        "text": (
            "Unlimited hay should make up 80 percent of a rabbit's diet as it is critical for "
            "dental wear and gut motility. Fresh leafy greens make up 15 percent and a small "
            "amount of pellets the remaining 5 percent. Fruits are treats only. Avoid sugary "
            "foods, starchy vegetables, and most commercial treats. Fresh water daily is essential."
        ),
        "metadata": {"species": "rabbit", "topic": "nutrition"},
    },
    {
        "id": "rabbit_vet_care",
        "text": (
            "Rabbits need annual vet checkups with an exotic animal specialist. Spaying and "
            "neutering is strongly recommended: unspayed females have up to 80 percent risk of "
            "uterine cancer by age 5. Teeth should be checked every 6 months as dental problems "
            "are common. GI stasis is a life-threatening emergency; signs include not eating, "
            "no fecal output, and a hunched posture."
        ),
        "metadata": {"species": "rabbit", "topic": "veterinary"},
    },
    # ---- General scheduling ------------------------------------------
    {
        "id": "scheduling_consistency",
        "text": (
            "Consistent daily schedules reduce anxiety in pets by making their day predictable. "
            "Feeding, walks, and playtime at the same times each day regulate the pet's internal "
            "clock. Irregular schedules lead to begging, destructive behavior, and stress. "
            "A schedule with high-priority tasks in the morning front-loads care before life "
            "events disrupt the day."
        ),
        "metadata": {"species": "general", "topic": "scheduling"},
    },
    {
        "id": "scheduling_conflicts",
        "text": (
            "Tasks scheduled at the same time create conflicts that often result in one task being "
            "skipped. Spacing tasks with at least 15-minute buffers improves completion rates. "
            "High-priority tasks like medication and feeding should be scheduled first and given "
            "dedicated time slots that do not overlap with other care activities."
        ),
        "metadata": {"species": "general", "topic": "scheduling"},
    },
    {
        "id": "vet_visit_importance",
        "text": (
            "Annual vet checkups catch conditions early when they are cheapest and easiest to treat. "
            "Senior pets (7 and older for dogs and cats) benefit from twice-yearly exams. "
            "A missing vet visit in a pet's care schedule is a significant gap. Many conditions "
            "including dental disease, kidney disease, and cancer are detectable before symptoms "
            "appear through routine bloodwork and physical examination."
        ),
        "metadata": {"species": "general", "topic": "veterinary"},
    },
]


def _build_store() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=_CHROMA_DIR)
    ef = DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=_COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    if collection.count() == 0:
        logger.info("Building pet care knowledge vector store (%d docs)", len(_KNOWLEDGE_DOCS))
        collection.add(
            ids=[d["id"] for d in _KNOWLEDGE_DOCS],
            documents=[d["text"] for d in _KNOWLEDGE_DOCS],
            metadatas=[d["metadata"] for d in _KNOWLEDGE_DOCS],
        )
        logger.info("Vector store ready.")
    else:
        logger.debug("Vector store already populated (%d docs).", collection.count())

    return collection


_collection: Optional[chromadb.Collection] = None


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        _collection = _build_store()
    return _collection


def retrieve(
    query: str,
    species_filter: Optional[list[str]] = None,
    n_results: int = 4,
) -> list[str]:
    """Return the top-n most relevant knowledge snippets for a given query.

    Args:
        query: Free-text question or context description.
        species_filter: If provided, restrict results to these species
                        plus general documents.
        n_results: Number of results to return.

    Returns:
        List of plain-text knowledge snippets ranked by relevance.
    """
    collection = _get_collection()

    where: Optional[dict] = None
    if species_filter:
        species_set = list(set(species_filter + ["general"]))
        if len(species_set) == 1:
            where = {"species": species_set[0]}
        else:
            where = {"species": {"$in": species_set}}

    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
            where=where,
        )
        docs = results.get("documents", [[]])[0]
        logger.info("RAG retrieved %d docs for query: %s", len(docs), query[:60])
        return docs
    except Exception as exc:
        logger.warning("RAG retrieval failed: %s", exc)
        return []
