import re
from typing import Dict, Any, List, Optional

# Prohibited safety keywords for moderation guardrail
PROHIBITED_KEYWORDS = {
    "drug", "cocaine", "weed", "weapon", "gun", "knife", "explosive",
    "hack", "fake id", "counterfeit", "stolen", "poison", "escort"
}

# Category Keyword Heuristics (Strictly whole-word boundaries to avoid substring false positives)
CATEGORY_KEYWORDS = {
    "Gardening": [
        "yard", "backyard", "front yard", "garden", "gardening", "lawn", "mow", "mowing",
        "weeds", "weeding", "hedges", "hedge", "plants", "leaves", "rake", "patio",
        "outdoor", "trim", "grass", "flowerbed", "overgrowth", "branch"
    ],
    "Moving Help": [
        "load", "loading", "truck", "van", "lorry", "boxes", "box", "furniture",
        "heavy lifting", "move", "moving", "unload", "unloading", "sofa", "couch",
        "mattress", "haul", "carry", "shift", "pack", "packing", "lift"
    ],
    "House Cleaning": [
        "vacuum", "mop", "dust", "deep clean", "tidy", "dishes", "cleaner",
        "bathroom", "kitchen", "oven", "windows", "carpet", "flat clean", "house clean",
        "clean house", "clean flat", "clean room", "clean inside", "sweep"
    ],
    "Pet Care": [
        "dog", "dogs", "cat", "cats", "pet", "pets", "puppy", "puppies", "kitten",
        "kittens", "retriever", "walk my dog", "walk the dog", "dog walk", "dog walking",
        "feed cat", "vet", "pet sit", "pet sitting", "foster"
    ],
    "Grocery Shopping": [
        "grocery", "groceries", "supermarket", "tesco", "sainsbury", "sainsburys",
        "asda", "aldi", "lidl", "morrisons", "m&s", "marks and spencer", "milk", "bread",
        "eggs", "shopping", "food store", "market run"
    ],
    "Pharmacy Pickup": [
        "pharmacy", "prescription", "prescriptions", "chemist", "boots", "medicine",
        "medication", "tablets", "pills", "inhaler", "pharmaceutical"
    ],
    "Delivery / Courier": [
        "parcel", "package", "deliver", "delivery", "courier", "post office", "royal mail",
        "dhl", "fedex", "shipment", "drop off", "send letter", "collect parcel"
    ],
    "Tech Support": [
        "computer", "laptop", "pc", "macbook", "printer", "wifi", "internet", "router",
        "phone setup", "tv setup", "install software", "troubleshoot"
    ],
    "Cooking / Meal Prep": [
        "cook", "cooking", "meal prep", "dinner", "lunch", "bake", "baking", "chef", "prepare food"
    ],
    "Car Wash": [
        "car wash", "wash car", "valet", "car detailing", "clean car", "vehicle wash"
    ],
    "Laundry": [
        "laundry", "ironing", "wash clothes", "dry clean", "dry cleaning", "fold clothes"
    ]
}

CATEGORY_BASE_PRICES = {
    "Grocery Shopping": 12.0,
    "Delivery / Courier": 9.0,
    "Pharmacy Pickup": 8.0,
    "Pet Care": 16.0,
    "House Cleaning": 22.0,
    "Gardening": 20.0,
    "Moving Help": 28.0,
    "Tech Support": 25.0,
    "Cooking / Meal Prep": 20.0,
    "Car Wash": 15.0,
    "Laundry": 12.0,
    "Other": 15.0,
}

KNOWN_AREAS = [
    "Elmfield Road", "Albany Road", "Wellfield Road", "Queen Street", "Newport Road",
    "City Road", "Roath", "Cathays", "Cardiff Bay", "Canton",
    "Penylan", "Llandaff", "Heath", "Whitchurch", "Bute Park", "Cyncoed"
]


def preprocess_text(text: str) -> str:
    """
    Normalizes conversational user input:
    - Separates stuck numbers & words: '40gordons' -> '40 gordons', '14maplewood' -> '14 maplewood'
    - Normalizes abbreviations: '10 a' -> '10 am', '7 p' -> '7 pm'
    - Normalizes comma spacing: '21 , pm' -> '21 pm'
    """
    t = text.strip()
    # 1. Unstick numbers glued to words (e.g. 40gordons -> 40 gordons), preserving ordinals (21st, 2nd, etc.)
    t = re.sub(r"\b(\d{1,4})(?!(?:st|nd|rd|th)\b)([a-zA-Z]{3,})\b", r"\1 \2", t)
    # 2. Normalize single letter am/pm with optional space/comma
    t = re.sub(r"\b(\d{1,2})\s*[,:]?\s*a\b", r"\1 am", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(\d{1,2})\s*[,:]?\s*p\b", r"\1 pm", t, flags=re.IGNORECASE)
    # 3. Clean up loose comma before am/pm: '21 , pm' -> '21 pm'
    t = re.sub(r"(\d{1,2})\s*,\s*(am|pm)\b", r"\1 \2", t, flags=re.IGNORECASE)
    return t


def check_content_safety(text: str) -> Dict[str, Any]:
    """Autonomous safety filter to guard against unsafe/illicit requests."""
    lower = text.lower()
    flagged = []
    for word in PROHIBITED_KEYWORDS:
        if re.search(rf"\b{re.escape(word)}\b", lower):
            flagged.append(word)

    is_safe = len(flagged) == 0
    return {
        "is_safe": is_safe,
        "flagged_keywords": flagged,
        "moderation_reason": "Content violates platform community safety guidelines." if not is_safe else "Clean"
    }


def extract_price(text: str) -> Optional[float]:
    """Extracts monetary offering from text (e.g., '£15.50', '20 pounds', 'paying 25 quid')."""
    # Pattern 1: £15 or £15.50
    m1 = re.search(r"£\s*(\d+(?:\.\d{1,2})?)", text)
    if m1:
        return float(m1.group(1))

    # Pattern 2: 15 pounds or 15 quid or paying 15
    m2 = re.search(r"\b(\d+(?:\.\d{1,2})?)\s*(?:gbp|pounds?|quid)\b", text, re.IGNORECASE)
    if m2:
        return float(m2.group(1))

    # Pattern 3: paying / offer / reward 15
    m3 = re.search(r"(?:paying|pay|offer|reward|budget)[:\s]+£?(\d+(?:\.\d{1,2})?)", text, re.IGNORECASE)
    if m3:
        return float(m3.group(1))

    return None


def extract_uk_postcode(text: str) -> Optional[str]:
    """Extracts UK postcode (e.g. CF24 9ZZ, CF10 3ND, CF24 3BA, CF24 9ZY)."""
    m = re.search(r"\b([A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2})\b", text, re.IGNORECASE)
    if m:
        code = m.group(1).upper()
        # Ensure standard space format e.g. 'CF24 9ZZ'
        if " " not in code and len(code) >= 5:
            code = code[:-3] + " " + code[-3:]
        return code
    return None


def extract_detailed_address(text: str) -> Dict[str, Any]:
    """
    Intelligent UK & Local Address Parser:
    Extracts house/building number, street name, secondary road/area, and UK postcode.
    Handles glued strings (40gordons road) and complex street combinations.
    """
    postcode = extract_uk_postcode(text)

    # 1. Look for street with number e.g. "17 st peters street", "40 gordons road", "14 maplewood street"
    street_with_no = None
    m_no = re.search(
        r"\b(\d{1,4}[a-zA-Z]?\s+(?:(?:st|saint)\s+)?[A-Za-z0-9\s]{2,25}?(?:street|st|road|rd|avenue|ave|lane|ln|drive|dr|terrace|crescent|cres|way|walk|close|court|gardens|place|square))\b",
        text,
        re.IGNORECASE
    )
    if m_no:
        street_with_no = m_no.group(1).strip().title()

    # 2. Look for secondary road/area mentioned (e.g. "Elmfield Road", "City Road")
    secondary_area = None
    for area in KNOWN_AREAS:
        if re.search(rf"\b{re.escape(area)}\b", text, re.IGNORECASE):
            # Avoid duplicating if same as street_with_no
            if not street_with_no or area.lower() not in street_with_no.lower():
                secondary_area = area
                break

    # 3. Assemble clean normalized address
    parts = []
    if street_with_no:
        parts.append(street_with_no)
    if secondary_area:
        parts.append(secondary_area)
    if postcode:
        parts.append(postcode)

    if parts:
        clean_address = ", ".join(parts)
    else:
        clean_address = "Cardiff, Local Area"

    return {
        "full_address": clean_address,
        "street_address": street_with_no,
        "area": secondary_area,
        "postcode": postcode,
    }


def extract_detailed_time(text: str) -> str:
    """
    Intelligent Temporal Extractor:
    Handles multi-component time clauses, e.g.:
    - 'time of the task 7pm 21st monday afternoon' -> 'Monday 21st at 7PM (Afternoon)'
    - 'monday 21 , pm' -> 'Monday at 21:00 (9:00 PM)'
    - 'time 10 a' / 'time 10 am' -> '10 AM'
    - 'tomorrow 4pm' -> 'Tomorrow 4pm'
    """
    lower = text.lower()

    # Pattern 1: Complex combo e.g. "time of the task 7pm 21st monday afternoon"
    m_task_time = re.search(
        r"\b(?:time\s*(?:of\s+(?:the\s+)?task)?[:\s]+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s+(\d{1,2}(?:st|nd|rd|th))\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+(morning|afternoon|evening|night))?",
        lower
    )
    if m_task_time:
        t_val = m_task_time.group(1).upper()
        d_val = m_task_time.group(2)
        day_val = m_task_time.group(3).capitalize()
        period = f" ({m_task_time.group(4).capitalize()})" if m_task_time.group(4) else ""
        return f"{day_val} {d_val} at {t_val}{period}"

    # Pattern 2: Day with hour number and am/pm e.g. "monday 21 , pm" or "monday 21 pm"
    m_day_num_pm = re.search(
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s*(\d{1,2})\s*(?:[:,]?\s*(am|pm))\b",
        lower
    )
    if m_day_num_pm:
        day = m_day_num_pm.group(1).capitalize()
        hour = int(m_day_num_pm.group(2))
        meridiem = m_day_num_pm.group(3).upper()
        if hour > 12:
            return f"{day} at {hour}:00 ({hour-12}:00 PM)"
        return f"{day} at {hour}:00 {meridiem}"

    # Pattern 3: Explicit time prefix e.g. "time 10 am", "time: 10am"
    m_time_only = re.search(r"\btime\s*(?:of\s+(?:the\s+)?task)?[:\s]+(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", lower)
    if m_time_only:
        return m_time_only.group(1).upper()

    # Pattern 4: today/tomorrow at [time]
    m_rel = re.search(r"\b(today|tomorrow)\s+(?:by|at|before)?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\b(?:morning|afternoon|evening))\b", lower)
    if m_rel:
        return f"{m_rel.group(1).capitalize()} {m_rel.group(2)}"

    # Pattern 5: [Day] [Hour] [am/pm]
    m_day_time = re.search(r"\b(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", lower)
    if m_day_time:
        return f"{m_day_time.group(1).capitalize()} at {m_day_time.group(2).upper()}"

    # Pattern 6: [Day] [Period]
    m_day_period = re.search(r"\b(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(morning|afternoon|evening|night)\b", lower)
    if m_day_period:
        return f"{m_day_period.group(1).capitalize()} {m_day_period.group(2).capitalize()}"

    # Pattern 7: Urgency markers
    if re.search(r"\b(asap|urgently|immediately)\b", lower):
        return "ASAP (Within 2 Hours)"

    return "Flexible / Open"


def clean_task_action(raw: str) -> str:
    """Normalizes the extracted action clause into a clean, human-readable task title."""
    # 1. Remove leading filler phrases
    cleaned = re.sub(r"^(to\s+|my\s+|a\s+|some\s+|help\s+me\s+to\s+|help\s+me\s+|please\s+)", "", raw, flags=re.IGNORECASE).strip()
    # 2. Split on trailing time/day/price/postcode expressions or condition remarks
    cleaned = re.split(
        r"\b(?:it\s*does\w*|it\s*is|its\s+not|not\s+too|as\s+long\s+as|time|paying|budget|reward|£|tomorrow|today|tonight|this\s+(?:morning|afternoon|evening|night|weekend|sunday|monday|tuesday|wednesday|thursday|friday|saturday)|on\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|in\s+[a-zA-Z]{1,2}\d{1,2}|at\s+\d)\b",
        cleaned,
        flags=re.IGNORECASE
    )[0].strip()
    # 3. Clean trailing punctuation
    cleaned = re.sub(r"[,;:\-\s]+$", "", cleaned).strip()
    return cleaned[:45].capitalize() if cleaned else "Community Task"


def extract_task_action(text: str) -> Dict[str, Any]:
    """
    Intelligent Task & Action Extractor:
    Isolates the actionable core of the user's errand, preventing address or timing
    chunks from being mistaken for the task.
    """
    # 1. Explicit task markers (excluding 'time of the task')
    m_explicit = re.findall(r"(?<!time of the )(?<!time for the )\b(?:task|errand|job)\s*[:\s-]+\s*([^,.;]+)", text, re.IGNORECASE)
    if m_explicit:
        action = clean_task_action(m_explicit[0])
        if len(action) >= 3:
            return {"raw_action": m_explicit[0].strip(), "task_name": action}

    # 2. Intent trigger clauses: 'i want someone to help me load things to a truck', 'need someone to clean my front yard'
    m_intent_verb = re.search(
        r"\b(?:i\s+want|want|i\s+need|need|looking\s+for|can\s+someone)\s+(?:someone|somone|somebody|help)?\s*(?:[a-zA-Z\s]{0,15}?)\s*(?:to|with)\s+([^,.;]+)",
        text,
        re.IGNORECASE
    )
    if m_intent_verb:
        action = clean_task_action(m_intent_verb.group(1))
        if len(action) >= 3:
            return {"raw_action": m_intent_verb.group(1).strip(), "task_name": action}

    # 3. Direct need / want + noun phrase: 'need car wash', 'need grocery run'
    m_need_noun = re.search(r"\b(?:need|want)\s+([a-zA-Z\s]{3,30}?)(?=\s+(?:today|tomorrow|at|by|on|paying|in\b|\.|$))", text, re.IGNORECASE)
    if m_need_noun:
        action = clean_task_action(m_need_noun.group(1))
        if len(action) >= 3:
            return {"raw_action": m_need_noun.group(1).strip(), "task_name": action}

    # 4. Action verb phrases: 'clean my backyard', 'load things to a truck', 'pick up my medication'
    m_verb = re.search(r"\b(clean|walk|load|unload|move|pick\s+up|deliver|buy|assemble|fix|mow|wash|tidy|iron)\s+([^,.;]+)", text, re.IGNORECASE)
    if m_verb:
        action = clean_task_action(m_verb.group(0))
        if len(action) >= 3:
            return {"raw_action": m_verb.group(0).strip(), "task_name": action}

    # 5. Fallback: Residual text extraction (subtracting address/postcode if present)
    residual = re.sub(r"\b(?:i\s+live\s+in|lives\s+in|live\s+in|at|from)\b.*?(?:street|road|avenue|lane|drive|terrace|close|[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2})", "", text, flags=re.IGNORECASE).strip()
    if residual:
        action = clean_task_action(residual)
        if len(action) >= 4 and action.lower() != "community task":
            return {"raw_action": residual, "task_name": action}

    return {
        "raw_action": "Community Task",
        "task_name": "Community Task",
    }


def infer_category(task_text: str, full_text: str = "") -> str:
    """
    Intelligent Category Classifier:
    Scores categories with strong priority (5x) on the isolated task action,
    avoiding false positives from address substrings (e.g. 'st peters' or 'maplewood').
    """
    task_lower = task_text.lower()
    full_lower = full_text.lower() if full_text else task_lower

    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            pattern = rf"\b{re.escape(kw)}\b"
            # Primary priority: direct match inside task clause
            if re.search(pattern, task_lower):
                score += 5
            # Secondary priority: match in full text (outside address)
            elif full_text and re.search(pattern, full_lower):
                score += 1

        if score > 0:
            scores[cat] = score

    if not scores:
        if "clean" in task_lower:
            return "House Cleaning"
        return "Other"

    return max(scores, key=scores.get)


def build_smart_title(task_name: str, location_name: Optional[str] = None) -> str:
    """Constructs a clean, professional errand listing title."""
    clean_task = task_name.strip()
    if location_name and location_name != "Cardiff, Local Area" and len(clean_task) <= 30:
        # Simplify location for title if it has multiple parts
        short_loc = location_name.split(",")[0].strip()
        # Abbreviate common road suffixes for title brevity
        short_loc = re.sub(r"\bStreet\b", "St", short_loc)
        short_loc = re.sub(r"\bRoad\b", "Rd", short_loc)
        short_loc = re.sub(r"\bAvenue\b", "Ave", short_loc)
        return f"{clean_task} - {short_loc}"
    return clean_task


def parse_errand_intent(raw_prompt: str) -> Dict[str, Any]:
    """
    Main Natural Language Pipeline:
    Converts unstructured voice/text input into categorized Address, Task,
    Time, Category, and Price entities with automated safety crosschecks.
    """
    # 1. Moderation & Safety check
    safety = check_content_safety(raw_prompt)
    if not safety["is_safe"]:
        return {
            "is_valid": False,
            "error": "Safety violation",
            "moderation": safety,
        }

    # 2. Preprocess text
    normalized_text = preprocess_text(raw_prompt)

    # 3. Extract components
    addr_info = extract_detailed_address(normalized_text)
    time_info = extract_detailed_time(normalized_text)
    task_info = extract_task_action(normalized_text)
    price = extract_price(normalized_text)

    # 4. Classify Category prioritizing the extracted task
    category = infer_category(task_info["task_name"], normalized_text)

    # 5. Smart Title
    task_label = task_info["task_name"]
    location_label = addr_info["street_address"] or addr_info["area"] or addr_info["full_address"]
    smart_title = build_smart_title(task_label, location_label)

    # 6. Fair price recommendation
    suggested_price = price if price is not None else CATEGORY_BASE_PRICES.get(category, 15.0)

    # 7. Keywords List for search indexing & visual pills
    keywords = []
    if addr_info["postcode"]:
        keywords.append(addr_info["postcode"])
    if addr_info["street_address"]:
        keywords.append(addr_info["street_address"])
    if addr_info["area"] and addr_info["area"] != addr_info["street_address"]:
        keywords.append(addr_info["area"])
    keywords.append(category)
    if task_label != "Community Task":
        keywords.append(task_label)
    if time_info != "Flexible / Open":
        keywords.append(time_info)

    return {
        "is_valid": True,
        "extracted": {
            "title": smart_title,
            "category": category,
            "price": float(suggested_price),
            "price_inferred": price is None,
            "location": addr_info["full_address"],
            "deadline": time_info,
            "description": raw_prompt.strip(),
        },
        "categorized_entities": {
            "address": addr_info["full_address"],
            "street": addr_info["street_address"],
            "area": addr_info["area"],
            "postcode": addr_info["postcode"],
            "task": task_label,
            "category": category,
            "time": time_info,
            "keywords": keywords,
        },
        "confidence": {
            "address_confidence": 0.95 if addr_info["postcode"] or addr_info["street_address"] else 0.70,
            "task_confidence": 0.95 if task_label != "Community Task" else 0.60,
            "time_confidence": 0.90 if time_info != "Flexible / Open" else 0.60,
            "category_confidence": 0.95 if category != "Other" else 0.60,
        },
        "moderation": safety
    }
