"""
MCP Tools: Text Processing

A collection of text analysis tools that work entirely offline
with no paid APIs. Agents select these tools dynamically based on
the task requirements.
"""

import os
import re
from collections import Counter

# ─── Common stopwords (no external dependency needed) ────────────────────────

STOP_WORDS = frozenset({
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "had",
    "her", "was", "one", "our", "out", "has", "have", "been", "that", "this",
    "with", "they", "from", "will", "each", "make", "like", "just", "over",
    "such", "than", "them", "some", "into", "its", "also", "more", "other",
    "would", "which", "their", "what", "about", "there", "when", "your",
    "could", "should", "these", "those", "where", "being", "does", "only",
    "most", "very", "much", "then", "here", "after", "before", "while",
})


# ─── Tool Functions ──────────────────────────────────────────────────────────

def read_text(file_path: str) -> dict:
    """Read content from a plain text or CSV file."""
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {
            "content": content,
            "chars": len(content),
            "lines": content.count("\n") + 1,
            "file": os.path.basename(file_path),
            "type": "text",
        }
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}


def extract_questions(text: str) -> dict:
    """Extract all questions from text content."""
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    questions = []
    seen = set()

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        # Direct question marks
        if sent.endswith("?") and sent not in seen:
            questions.append(sent)
            seen.add(sent)

    # Also find numbered/bulleted questions that may not end with ?
    pattern = r'(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:What|How|Why|When|Where|Who|Which|Can|Do|Does|Is|Are|Will|Should|Could|Would)[^\n.]*\?'
    for match in re.findall(pattern, text, re.IGNORECASE | re.MULTILINE):
        q = match.strip()
        if q not in seen:
            questions.append(q)
            seen.add(q)

    return {"questions": questions, "count": len(questions)}


def summarize_text(text: str, num_sentences: int = 5) -> dict:
    """
    Extractive summarization using TF-based sentence scoring.
    No LLM required — purely algorithmic.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if not sentences:
        return {"summary": text[:500] if text else "(empty)", "method": "truncation"}

    if len(sentences) <= num_sentences:
        return {"summary": " ".join(sentences), "method": "full_text"}

    # Build word frequency map
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    word_freq = Counter(w for w in words if w not in STOP_WORDS)

    if not word_freq:
        return {"summary": " ".join(sentences[:num_sentences]), "method": "first_n"}

    max_freq = max(word_freq.values())
    normalized = {w: freq / max_freq for w, freq in word_freq.items()}

    # Score each sentence by average word importance
    scored = []
    for i, sent in enumerate(sentences):
        words_in = re.findall(r'\b[a-z]{3,}\b', sent.lower())
        if words_in:
            score = sum(normalized.get(w, 0) for w in words_in) / len(words_in)
            scored.append((score, i, sent))

    # Select top sentences, preserve original order
    scored.sort(reverse=True)
    top = scored[:num_sentences]
    top.sort(key=lambda x: x[1])  # restore document order

    summary = " ".join(sent for _, _, sent in top)
    return {
        "summary": summary,
        "method": "extractive_tf",
        "sentences_selected": len(top),
        "total_sentences": len(sentences),
    }


def extract_keywords(text: str, top_n: int = 10) -> dict:
    """Extract the most important keywords from text using term frequency."""
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    word_freq = Counter(w for w in words if w not in STOP_WORDS)
    top = word_freq.most_common(top_n)
    return {
        "keywords": [w for w, _ in top],
        "frequencies": dict(top),
        "total_unique_words": len(word_freq),
    }


def analyze_tabular_data(headers: list, rows: list) -> dict:
    """Analyze tabular/spreadsheet data and generate statistical insights."""
    if not rows or not headers:
        return {"error": "No data to analyze"}

    insights = []
    column_stats = {}

    for i, header in enumerate(headers):
        if not header:
            continue
        values = [row[i] for row in rows if i < len(row) and row[i] not in (None, "")]

        # Attempt numeric analysis
        numeric_vals = []
        for v in values:
            try:
                numeric_vals.append(float(v))
            except (ValueError, TypeError):
                pass

        if numeric_vals and len(numeric_vals) >= 2:
            sorted_v = sorted(numeric_vals)
            mid = len(sorted_v) // 2
            median = sorted_v[mid] if len(sorted_v) % 2 else (sorted_v[mid - 1] + sorted_v[mid]) / 2
            mean = sum(numeric_vals) / len(numeric_vals)
            stats = {
                "type": "numeric",
                "count": len(numeric_vals),
                "min": min(numeric_vals),
                "max": max(numeric_vals),
                "mean": round(mean, 2),
                "median": round(median, 2),
                "sum": round(sum(numeric_vals), 2),
            }
            column_stats[header] = stats
            insights.append(
                f"'{header}': numeric, range [{stats['min']}–{stats['max']}], "
                f"mean={stats['mean']}, median={stats['median']}"
            )
        elif values:
            # Categorical analysis
            value_counts = Counter(str(v) for v in values)
            most_common = value_counts.most_common(3)
            stats = {
                "type": "categorical",
                "count": len(values),
                "unique": len(value_counts),
                "most_common": most_common,
            }
            column_stats[header] = stats
            top_label = most_common[0][0] if most_common else "N/A"
            insights.append(
                f"'{header}': categorical, {len(value_counts)} unique values, "
                f"most common: '{top_label}'"
            )

    return {
        "row_count": len(rows),
        "column_count": len(headers),
        "column_stats": column_stats,
        "insights": insights,
    }
