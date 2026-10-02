"""
SmartCampus AI — Real NLP Triage Service

Provides deterministic & AI NLP triage for student complaints:
  - Multi-keyword category & department classification (Electrical, Plumbing, IT, Security, etc.)
  - Urgency & safety-critical threat detection (fire, smoke, shock, gas leak, injury)
  - Jaccard semantic similarity duplicate report detection
  - Text summarization and sentiment analysis
  - Predicted SLA timeline and duty officer assignment
"""

import re
from typing import List, Dict, Any, Tuple
from app.models.complaint import ComplaintPriority


AI_RULES = [
    {
        "cat": "Electrical",
        "dept": "Electrical Maintenance",
        "kw": ["power", "electric", "light", "fan", "socket", "switch", "current", "shock", "wiring", "outage", "bulb", "sparking", "short circuit", "voltage", "charging", "sockets"],
        "action": "Dispatch electrician for on-site inspection. Isolate circuit if sparking/smell reported."
    },
    {
        "cat": "Plumbing",
        "dept": "Plumbing & Water",
        "kw": ["water", "leak", "tap", "pipe", "drain", "washroom", "toilet", "sink", "sewage", "bathroom", "seepage", "overflow", "drinking"],
        "action": "Send plumber to inspect line/valve. Shut off supply if active flooding."
    },
    {
        "cat": "Network & WiFi",
        "dept": "IT & Network Services",
        "kw": ["wifi", "wi-fi", "internet", "network", "lan", "router", "connectivity", "signal", "portal", "broadband", "hotspot"],
        "action": "Check access point/controller status. Reset AP and verify DHCP/DNS."
    },
    {
        "cat": "IT Support",
        "dept": "IT & Network Services",
        "kw": ["projector", "computer", "printer", "software", "laptop", "hdmi", "display", "av", "screen", "keyboard", "system"],
        "action": "Assign AV/IT technician with spare unit. Test all inputs on arrival."
    },
    {
        "cat": "Cleanliness",
        "dept": "Housekeeping",
        "kw": ["clean", "garbage", "dust", "waste", "dirty", "sweep", "trash", "hygiene", "smell", "bins", "overflowing", "mosquito"],
        "action": "Schedule extra housekeeping round. Clear waste and sanitize area."
    },
    {
        "cat": "Food & Canteen",
        "dept": "Food & Canteen",
        "kw": ["food", "canteen", "mess", "meal", "lunch", "dinner", "breakfast", "stale", "hygiene", "thali", "cafeteria", "kitchen"],
        "action": "Notify vendor + food safety officer. Collect samples and audit kitchen."
    },
    {
        "cat": "Security",
        "dept": "Campus Security",
        "kw": ["security", "unsafe", "theft", "steal", "street light", "dark", "cctv", "guard", "suspicious", "safety", "parking"],
        "action": "Increase patrols in area. Verify CCTV coverage and lighting."
    },
    {
        "cat": "Transport",
        "dept": "Transport Cell",
        "kw": ["bus", "transport", "route", "driver", "late", "cab", "shuttle", "vehicle", "gps"],
        "action": "Pull GPS logs and review timetable adherence with vendor."
    },
    {
        "cat": "Library",
        "dept": "Central Library",
        "kw": ["library", "book", "reading", "study hall", "journal", "membership"],
        "action": "Coordinate with library staff for access/facility fix."
    },
    {
        "cat": "Hostel",
        "dept": "Hostel Office",
        "kw": ["hostel", "warden", "room", "mess timing", "allotment", "curfew", "roommate"],
        "action": "Route to hostel warden with occupancy details for resolution."
    },
    {
        "cat": "Civil & Infrastructure",
        "dept": "Civil & Infrastructure",
        "kw": ["ac", "air condition", "wall", "crack", "tile", "ceiling", "door", "window", "lift", "elevator", "building", "furniture", "bench", "seepage", "repair", "construction", "hot"],
        "action": "Raise civil work order. Schedule vendor visit with materials."
    },
]

CRITICAL_KW = ["fire", "smoke", "shock", "electrocution", "burning smell", "burning", "sparking", "short circuit", "flood", "burst", "emergency", "gas leak", "injury", "blood", "collapse", "falling", "wobbling dangerously", "unsafe"]
HIGH_KW = ["no power", "no water", "completely down", "not working", "broken", "blocked", "outage", "stuck", "overflow", "leakage", "three days", "unsafe", "unable", "urgent", "symposium", "submission", "due today", "foreign object", "plastic", "stale"]
MED_KW = ["slow", "dim", "noise", "crack", "repair", "replace", "late", "hot", "dirty", "smell", "issue", "problem", "request"]

OFFICERS = {
    "Electrical Maintenance": "Rahul Verma",
    "Plumbing & Water": "Suresh Kumar",
    "IT & Network Services": "Priya Nair",
    "Housekeeping": "Meena Joshi",
    "Hostel Office": "Hostel Warden",
    "Campus Security": "Vikram Singh",
    "Transport Cell": "Arun Pillai",
    "Central Library": "Library Desk",
    "Food & Canteen": "Kavita Rao",
    "Civil & Infrastructure": "Deepak Yadav"
}


def _tokenize(text: str) -> List[str]:
    return [w for w in re.sub(r"[^a-z0-9\s]", " ", text.lower()).split() if len(w) > 2]


def _jaccard_similarity(text1: str, text2: str) -> float:
    tokens1 = set(_tokenize(text1))
    tokens2 = set(_tokenize(text2))
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union)


class AITriageService:
    """Core NLP Engine for Complaint Categorization, Urgency Triage & Duplicate Detection."""

    @staticmethod
    def analyze(title: str, description: str, location: str = "", existing_complaints: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        full_text = f"{title} {description} {location}".lower()
        
        # 1. Category & Department Classification
        best_rule = {
            "cat": "General",
            "dept": "Hostel Office",
            "score": 0,
            "action": "Route to campus helpdesk for manual review."
        }
        
        for rule in AI_RULES:
            score = 0
            for kw in rule["kw"]:
                if kw in full_text:
                    score += 3 if " " in kw else 2
            if score > best_rule["score"]:
                best_rule = {
                    "cat": rule["cat"],
                    "dept": rule["dept"],
                    "score": score,
                    "action": rule["action"]
                }
                
        # 2. Urgency Detection
        urgency = ComplaintPriority.LOW
        reason = "Routine request with no time-sensitive or safety language detected."
        
        if any(kw in full_text for kw in CRITICAL_KW):
            urgency = ComplaintPriority.CRITICAL
            reason = "Safety-critical language detected (fire / shock / flooding / injury risk). Auto-escalated."
        elif any(kw in full_text for kw in HIGH_KW):
            urgency = ComplaintPriority.HIGH
            reason = "Service outage / breakage / deadline-impacting language detected."
        elif any(kw in full_text for kw in MED_KW):
            urgency = ComplaintPriority.MEDIUM
            reason = "Functional issue affecting comfort or daily routine."

        # 3. Confidence Score
        confidence = min(98, max(72, 74 + best_rule["score"] * 4 + (6 if urgency == ComplaintPriority.CRITICAL else 0)))

        # 4. Sentiment Detection
        sentiment = "Neutral"
        if re.search(r"angry|plastic|stale|worst|terrible|pathetic|disgusting", full_text):
            sentiment = "Angry"
        elif re.search(r"urgent|emergency|scared|dangerous|unsafe|fear", full_text):
            sentiment = "Urgent"
        elif re.search(r"frustrat|annoy|tired|again|still|days", full_text):
            sentiment = "Frustrated"
        elif re.search(r"please|request|kindly|suggest", full_text):
            sentiment = "Polite"
        elif re.search(r"worried|concern", full_text):
            sentiment = "Concerned"

        # 5. ETA Prediction
        eta_map = {
            ComplaintPriority.CRITICAL: "~6 hours",
            ComplaintPriority.HIGH: "~1 day",
            ComplaintPriority.MEDIUM: "~3 days",
            ComplaintPriority.LOW: "~5 days"
        }
        eta = eta_map.get(urgency, "~2 days")

        # 6. Keywords Extraction
        all_tokens = _tokenize(f"{title} {description}")
        stop_words = {"the", "and", "for", "with", "this", "that", "have", "has", "been", "from", "are", "was", "were", "will", "they", "them", "there", "here", "please", "since", "every", "about"}
        keywords = list(dict.fromkeys([w for w in all_tokens if w not in stop_words]))[:6]

        # 7. Summary Generation
        sentences = [s.strip() for s in re.split(r"[.!?]", description) if len(s.strip()) > 10]
        summary = sentences[0][:140] if sentences else description[:140]

        # 8. Duplicate Detection
        duplicates = []
        if existing_complaints:
            for item in existing_complaints:
                sim = _jaccard_similarity(f"{title} {description}", f"{item.get('title', '')} {item.get('description', '')}")
                if sim > 0.22:
                    duplicates.append({
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "similarity_score": round(sim, 2)
                    })
            duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)
            duplicates = duplicates[:2]

        assigned_officer = OFFICERS.get(best_rule["dept"], "Duty Officer")

        return {
            "category": best_rule["cat"],
            "department": best_rule["dept"],
            "urgency": urgency,
            "confidence": confidence,
            "duplicates": duplicates,
            "summary": summary,
            "keywords": keywords,
            "sentiment": sentiment,
            "eta": eta,
            "suggested_action": best_rule["action"],
            "reason": reason,
            "assigned_officer": assigned_officer
        }
