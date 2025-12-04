from typing import Dict, Optional
import textwrap
from .text_cleaner import split_by_headings
import os

def _first_paragraph_of_section(headings: Dict[str,str], keys):
    for k in keys:
        if k in headings:
            sec = headings[k].strip()
            # return first 600 chars (approx one paragraph)
            return sec.split("\n\n")[0].strip()
    return ""

def extract_methodology(text: str, headings: Optional[Dict[str,str]] = None, use_openai: bool=False) -> str:
    """
    Extract methodology using heuristics: prefer explicit Method/Methodology/Experiment sections.
    If not found, fall back to scanning sentences that mention 'we' and verbs like 'propose', 'use', 'collect'.
    """
    if headings is None:
        headings = split_by_headings(text)
    # Preferred headings
    method = _first_paragraph_of_section(headings, ["methodology", "method", "materials", "experiment", "experiments"])
    if method:
        return _clean_and_shorten(method, "Methodology")
    # fallback heuristic
    lines = text.split("\n")
    candidates = [ln for ln in lines if any(w in ln.lower() for w in ["we used", "we propose", "we used", "we implement", "we collect", "we propose", "our approach", "we perform", "we propose"])]
    if candidates:
        return _clean_and_shorten("\n".join(candidates[:5]), "Methodology")
    # last resort: top 800 chars
    return _clean_and_shorten(text[:1500], "Methodology")

def extract_contributions(text: str, headings: Optional[Dict[str,str]] = None, use_openai: bool=False) -> str:
    if headings is None:
        headings = split_by_headings(text)
    contrib = _first_paragraph_of_section(headings, ["contributions"])
    if contrib:
        return _clean_and_shorten(contrib, "Contributions")
    # sometimes contributions are in introduction or conclusion
    contrib = _first_paragraph_of_section(headings, ["introduction", "conclusion", "conclusions", "discussion"])
    if contrib:
        # look for lines starting with "we" and containing "contribute"/"contribution" or "novel"
        lines = [ln for ln in contrib.split("\n") if any(k in ln.lower() for k in ["contrib", "novel", "we propose", "we present", "this paper"])]
        if lines:
            return _clean_and_shorten("\n".join(lines[:8]), "Contributions")
    # fallback: scan for sentences with "we" and "novel"/"contribute"
    sentences = [s.strip() for s in text.replace("\n"," ").split(".") if s.strip()]
    candidates = [s for s in sentences if any(k in s.lower() for k in ["contrib", "novel", "we propose", "we present", "we introduce"])]
    if candidates:
        return _clean_and_shorten(". ".join(candidates[:4]) + ".", "Contributions")
    return "No explicit contributions section found. Consider reading Abstract/Introduction/Conclusion for contributions."

def extract_results(text: str, headings: Optional[Dict[str,str]] = None, use_openai: bool=False) -> str:
    if headings is None:
        headings = split_by_headings(text)
    res = _first_paragraph_of_section(headings, ["results", "discussion"])
    if res:
        return _clean_and_shorten(res, "Results")
    # fallback: look near conclusion or abstract for numeric mentions
    res = _first_paragraph_of_section(headings, ["abstract", "conclusion", "conclusions"])
    if res:
        # extract sentences that look like result statements (accuracy, improvement, outperform, achieves)
        sentences = [s.strip() for s in res.replace("\n"," ").split(".") if s.strip()]
        candidates = [s for s in sentences if any(k in s.lower() for k in ["accuracy", "%", "improv", "outperform", "achiev", "result", "show"])]
        if candidates:
            return _clean_and_shorten(". ".join(candidates[:5]) + ".", "Results")
    # general fallback: find sentences with numbers / % signs in whole text
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    candidates = [s for s in sentences if any(ch.isdigit() for ch in s) and len(s) < 350]
    if candidates:
        return _clean_and_shorten(". ".join(candidates[:6]) + ".", "Results")
    return "No explicit numeric results found. Please check Results/Discussion section in the paper."

def generate_summary(text: str, use_openai: bool=False) -> str:
    """
    Generate a concise summary. If use_openai=True and OPENAI_API_KEY set, uses OpenAI. Otherwise rule-based extractive summary.
    """
    if use_openai and os.getenv("OPENAI_API_KEY"):
        # Optional: If you want to use OpenAI, uncomment the block below and install openai.
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            prompt = (
                "You are a research assistant. Provide a concise 4-6 sentence summary of the following research paper text. "
                "Limit to 120-160 words and write as a single paragraph.\n\n"
                f"{text[:4000]}"
            )
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini", # adjust model name as desired / available
                messages=[{"role":"user","content":prompt}],
                max_tokens=300,
                temperature=0.2
            )
            summary = resp["choices"][0]["message"]["content"].strip()
            return summary
        except Exception as e:
            # fallback to local method
            pass

    # Local extractive summary: pick key paragraphs: abstract, intro first para, conclusion first para, top sentences with numbers
    from .text_cleaner import split_by_headings
    headings = split_by_headings(text)
    pieces = []
    if "abstract" in headings:
        pieces.append(headings["abstract"].split("\n\n")[0])
    if "introduction" in headings:
        pieces.append(headings["introduction"].split("\n\n")[0])
    if "conclusion" in headings:
        pieces.append(headings["conclusion"].split("\n\n")[0])
    # add first paragraph from method and results if available
    for k in ["methodology", "method", "results"]:
        if k in headings:
            pieces.append(headings[k].split("\n\n")[0])
    # join and then compress naively by taking top N sentences (by heuristic: sentences with keywords)
    big = " ".join(pieces).strip()
    if not big:
        big = text[:4000]
    sentences = [s.strip() for s in big.split(".") if s.strip()]
    # prefer sentences with keywords
    keywords = ["propose", "present", "show", "result", "achieve", "demonstrate", "improve", "approach", "method", "contribution"]
    ranked = []
    for s in sentences:
        score = sum(1 for k in keywords if k in s.lower())
        score += len([c for c in s if c.isdigit()])  # small bias to numeric statements
        ranked.append((score, s))
    ranked.sort(reverse=True, key=lambda x: x[0])
    top = [s for _, s in ranked[:6]]
    summary = ". ".join(top).strip()
    if not summary:
        summary = "Summary could not be extracted. Try using OpenAI option or check that PDF contains selectable text."
    # tidy up
    return textwrap.shorten(summary, width=1200, placeholder="...")

def _clean_and_shorten(text: str, label: str) -> str:
    # remove excessive whitespace
    import re
    t = re.sub(r"\s{2,}", " ", text).strip()
    # ensure it's not gigantic
    if len(t) > 2000:
        t = t[:1900] + "..."
    return t
