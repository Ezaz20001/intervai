import re
from typing import Dict, Any, List

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


FILLER_WORDS = {
    "um", "uh", "like", "you know", "actually", "basically", "literally",
    "honestly", "i mean", "sort of", "kind of", "well", "so", "right",
}

_sentiment_analyzer = None


def _get_sentiment():
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentIntensityAnalyzer()
    return _sentiment_analyzer


def analyze_text(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    words = text_lower.split()
    word_count = len(words)
    char_count = len(text)

    filler_found = []
    for fw in FILLER_WORDS:
        count = len(re.findall(r'\b' + re.escape(fw) + r'\b', text_lower))
        if count > 0:
            filler_found.append({"word": fw, "count": count})

    filler_count = sum(f["count"] for f in filler_found)
    filler_density = round(filler_count / word_count, 3) if word_count > 0 else 0

    sentences = re.split(r"[.!?]+", text)
    avg_sentence_length = round(word_count / len(sentences), 1) if sentences else 0

    sentiment = _get_sentiment().polarity_scores(text)

    speaking_rate_wpm = word_count
    pause_count = text.count("...") + text.count(" -- ") + text.count(", ") // 3

    confidence_score = _estimate_confidence(sentiment, filler_density, avg_sentence_length)

    return {
        "word_count": word_count,
        "char_count": char_count,
        "filler_words": filler_found,
        "filler_count": filler_count,
        "filler_density": filler_density,
        "avg_sentence_length": avg_sentence_length,
        "sentiment": sentiment,
        "speaking_rate_wpm": speaking_rate_wpm,
        "pause_indicators": pause_count,
        "confidence_score": confidence_score,
    }


def _estimate_confidence(
    sentiment: Dict[str, float],
    filler_density: float,
    avg_sentence_length: float,
) -> float:
    score = 5.0
    score += (sentiment["pos"] - sentiment["neg"]) * 3
    score -= filler_density * 15
    if avg_sentence_length < 4:
        score -= 1
    elif avg_sentence_length > 20:
        score += 1
    return round(max(1.0, min(10.0, score)), 1)


def get_overall_communication_score(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not analyses:
        return {"overall_score": 0, "avg_confidence": 0, "total_fillers": 0}

    avg_conf = round(sum(a["confidence_score"] for a in analyses) / len(analyses), 1)
    total_fillers = sum(a["filler_count"] for a in analyses)
    avg_sentiment_pos = round(
        sum(a["sentiment"]["pos"] for a in analyses) / len(analyses), 3
    )
    avg_sentiment_neg = round(
        sum(a["sentiment"]["neg"] for a in analyses) / len(analyses), 3
    )

    overall = round((avg_conf + (1 - avg_sentiment_neg) * 5) / 2, 1)

    return {
        "overall_score": overall,
        "avg_confidence": avg_conf,
        "total_fillers": total_fillers,
        "avg_sentiment_positive": avg_sentiment_pos,
        "avg_sentiment_negative": avg_sentiment_neg,
    }
