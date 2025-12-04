import re
from typing import Dict, List

def clean_text(text: str) -> str:
    # Basic cleaning: remove extra whitespace, fix hyphenation, normalize newlines
    if not text:
        return ""
    # fix hyphenation at line breaks
    text = re.sub(r"-\n\s*", "", text)
    # replace multiple newlines with two
    text = re.sub(r"\n{3,}", "\n\n", text)
    # trim leading/trailing spaces on lines
    text = "\n".join([ln.strip() for ln in text.splitlines() if ln.strip() != ""])
    return text.strip()

def split_by_headings(text: str) -> Dict[str, str]:
    """
    Heuristic split: find common headings like Method, Methodology, Results, Conclusion, Contribution, Abstract
    Return a dict mapping heading -> section text (best-effort).
    """
    headings = ["abstract", "introduction", "background", "related work", "method", "methodology",
                "materials", "experiment", "experiments", "results", "conclusion", "conclusions",
                "contributions", "discussion", "future work", "references"]
    # Create a regex to find headings lines
    pattern = r"(?m)^(?:{0})\s*$".format("|".join([re.escape(h) for h in headings]))
    # find positions (case-insensitive)
    matches = []
    for m in re.finditer(r"(?mi)^(%s)\.?:?\s*$" % "|".join(headings), text, flags=0):
        matches.append((m.group(1).lower(), m.start()))
    # If no headings found, return empty dict
    if not matches:
        return {}
    # Build ranges
    sections = {}
    for i, (h, pos) in enumerate(matches):
        start = pos
        end = matches[i+1][1] if i+1 < len(matches) else len(text)
        snippet = text[start:end].strip()
        sections[h] = snippet
    return sections
