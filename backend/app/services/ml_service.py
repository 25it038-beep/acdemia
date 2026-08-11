import logging
import math
import re
import string
from collections import Counter
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Text utilities ────────────────────────────────────────────────────────────

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", "while",
    "for", "to", "of", "in", "on", "at", "by", "with", "from", "as", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "shall", "should", "may", "might", "must", "can",
    "could", "this", "that", "these", "those", "there", "here", "where", "which",
    "who", "whom", "whose", "what", "why", "how", "not", "no", "yes", "so", "too",
    "very", "just", "also", "only", "own", "same", "such", "than", "then", "into",
    "over", "under", "again", "further", "once", "each", "more", "most", "other",
    "some", "any", "both", "all", "few", "many", "much", "per", "via", "within",
    "without", "about", "against", "between", "through", "during", "before",
    "after", "above", "below", "up", "down", "out", "off", "your", "you", "we",
    "they", "it", "its", "their", "our", "us", "them", "his", "her", "him", "she",
    "he", "i", "me", "my", "etc", "e.g", "i.e", "eg", "ie", "vs", "versus", "please",
    "note", "however", "therefore", "thus", "hence", "according", "using", "used",
    "use", "can", "may", "must", "will", "one", "two", "three", "four", "five",
    "first", "second", "third", "last", "next", "new", "old", "different", "important",
}


def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, split on non-alpha, drop stopwords/short tokens."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = [t for t in re.split(r"\s+", text) if len(t) >= 3 and t not in STOPWORDS]
    return tokens


def _count_sentences(text: str) -> int:
    sentences = re.split(r"[.!?]+", text)
    return max(1, len([s for s in sentences if s.strip()]))


def _count_words(text: str) -> int:
    return max(1, len([w for w in re.split(r"\s+", text) if w.strip()]))


def _count_syllables(word: str) -> int:
    """Approximate syllable count using the vowel-group heuristic."""
    word = word.lower()
    if not word:
        return 1
    count = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


# ── Readability (Flesch-Kincaid + ARI) ────────────────────────────────────────

def _flesch_kincaid(text: str) -> Dict[str, float]:
    words = _count_words(text)
    sentences = _count_sentences(text)
    syllables = sum(_count_syllables(w) for w in re.findall(r"[a-zA-Z]+", text))
    if words <= 1:
        return {"flesch_reading_ease": 100.0, "flesch_kincaid_grade": 0.0}
    fk_grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
    fre = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    return {
        "flesch_reading_ease": round(max(0.0, min(100.0, fre)), 1),
        "flesch_kincaid_grade": round(max(0.0, fk_grade), 1),
    }


def _automated_readability_index(text: str) -> float:
    words = _count_words(text)
    sentences = _count_sentences(text)
    characters = len(re.findall(r"[a-zA-Z0-9]", text))
    if sentences == 0:
        return 0.0
    ari = 4.71 * (characters / words) + 0.5 * (words / sentences) - 21.43
    return round(max(0.0, ari), 1)


# ── Subject classification (curriculum keyword bank) ──────────────────────────

SUBJECT_KEYWORDS: Dict[str, List[str]] = {
    "Mathematics": [
        "algebra", "calculus", "derivative", "integral", "equation", "theorem",
        "matrix", "vector", "geometry", "trigonometry", "polynomial", "function",
        "limit", "differential", "probability", "statistics", "integer", "fraction",
        "linear", "quadratic", "exponent", "logarithm", "summation", "series",
        "manifold", "topology", "graph theory", "number theory", "combinatorics",
        "eigenvalue", "determinant", "proof", "axiom", "lemma",
    ],
    "Computer Science": [
        "algorithm", "data structure", "programming", "python", "java", "javascript",
        "compiler", "operating system", "database", "sql", "networking", "protocol",
        "encryption", "machine learning", "artificial intelligence", "neural",
        "deep learning", "api", "framework", "binary", "byte", "recursion", "loop",
        "function", "variable", "class", "object", "inheritance", "encapsulation",
        "pointer", "memory", "thread", "process", "linux", "git", "html", "css",
        "software", "debugging", "complexity", "stack", "queue", "tree", "hash",
    ],
    "Physics": [
        "force", "mass", "velocity", "acceleration", "momentum", "energy", "work",
        "power", "newton", "gravity", "electricity", "magnetism", "magnetic",
        "electric field", "quantum", "relativity", "photon", "electron", "atom",
        "nuclear", "wavelength", "frequency", "amplitude", "wave", "kinematics",
        "thermodynamics", "entropy", "heat", "temperature", "friction", "pressure",
        "optics", "lens", "mirror", "refraction", "diffraction", "circuit", "voltage",
        "current", "resistance", "capacitor",
    ],
    "Chemistry": [
        "atom", "molecule", "element", "compound", "reaction", "chemical", "bond",
        "covalent", "ionic", "hydrogen", "oxygen", "carbon", "nitrogen", "acid",
        "base", "ph", "salt", "solution", "concentration", "molarity", "stoichiometry",
        "organic", "inorganic", "polymer", "catalyst", "enzyme", "oxidation",
        "reduction", "redox", "periodic", "valence", "electron", "proton", "neutron",
        "isotope", "mole", "gas", "liquid", "solid", "distillation", "titration",
    ],
    "Biology": [
        "cell", "dna", "rna", "gene", "protein", "organism", "evolution", "species",
        "ecosystem", "photosynthesis", "respiration", "enzyme", "chromosome",
        "mutation", "bacteria", "virus", "immunity", "tissue", "organ", "hormone",
        "nervous", "neuron", "anatomy", "physiology", "genetics", "reproduction",
        "metabolism", "homeostasis", "mitochondria", "nucleus", "membrane",
        "biodiversity", "habitat", "climate", "digestion", "circulation",
    ],
    "Economics": [
        "supply", "demand", "market", "price", "inflation", "gdp", "trade",
        "import", "export", "tax", "interest", "investment", "capital", "labor",
        "production", "consumption", "marginal", "elasticity", "monopoly",
        "competition", "fiscal", "monetary", "recession", "unemployment", "currency",
        "exchange", "welfare", "budget", "deficit", "surplus", "utility", "scarce",
    ],
    "Business": [
        "management", "marketing", "strategy", "organization", "leadership",
        "finance", "accounting", "audit", "entrepreneurship", "startup", "brand",
        "customer", "sales", "revenue", "profit", "operations", "supply chain",
        "human resources", "stakeholder", "corporate", "innovation", "merger",
        "acquisition", "business model", "market share", "value chain",
    ],
    "Engineering": [
        "circuit", "mechanical", "civil", "electrical", "structural", "hydraulic",
        "materials", "stress", "strain", "beam", "load", "turbine", "engine",
        "robotics", "automation", "control system", "signal", "sensor", "actuator",
        "thermodynamic cycle", "machine", "manufacturing", "cad", "blueprint",
        "static", "dynamic", "fluid", "electromagnetic", "semiconductor", "chip",
    ],
    "Medicine": [
        "patient", "disease", "symptom", "diagnosis", "treatment", "therapy",
        "surgery", "drug", "dose", "clinical", "infection", "inflammation", "tumor",
        "cancer", "diabetes", "cardiac", "pulmonary", "renal", "hepatic", "immune",
        "vaccine", "antibiotic", "symptom", "syndrome", "anatomy", "pathology",
        "pharmacology", "prognosis", "acute", "chronic", "pediatric",
    ],
    "Psychology": [
        "behavior", "cognition", "perception", "emotion", "memory", "learning",
        "motivation", "personality", "psychotherapy", "depression", "anxiety",
        "stress", "cognitive", "developmental", "social psychology", "consciousness",
        "attention", "perception", "neuroscience", "psychoanalysis", "conditioning",
        "intelligence", "attachment", "trauma", "mental health",
    ],
    "Law": [
        "statute", "legislation", "contract", "tort", "criminal", "civil law",
        "constitution", "amendment", "jurisdiction", "liability", "plaintiff",
        "defendant", "verdict", "appeal", "hearing", "testimony", "evidence",
        "clause", "arbitration", "litigation", "intellectual property", "patent",
        "copyright", "trademark", "regulation", "compliance", "attorney",
    ],
    "Data Science": [
        "dataset", "regression", "classification", "clustering", "feature",
        "model training", "prediction", "bias", "variance", "pandas", "numpy",
        "scikit", "tensorflow", "pytorch", "embedding", "tokenization", "nlp",
        "natural language", "timeseries", "time series", "correlation", "outlier",
        "normalization", "cross-validation", "overfitting", "gradient", "descent",
    ],
    "Literature": [
        "novel", "poem", "poetry", "prose", "narrative", "character", "plot",
        "theme", "symbolism", "metaphor", "allegory", "genre", "fiction",
        "nonfiction", "author", "protagonist", "antagonist", "dialogue", "stanza",
        "verse", "literary", "essay", "drama", "tragedy", "comedy", "satire",
    ],
    "History": [
        "war", "empire", "revolution", "kingdom", "treaty", "century", "dynasty",
        "civilization", "colony", "colonial", "monarchy", "republic", "invasion",
        "renaissance", "medieval", "ancient", "industrial revolution", "cold war",
        "world war", "archaeology", "chronicle", "era", "reform", "independence",
        "constitution", "ruler", "conquest",
    ],
}


def classify_subject(tokens: List[str], top_n: int = 3) -> List[Dict]:
    """Score the document against curriculum keyword banks; returns ranked subjects."""
    if not tokens:
        return []
    token_counts = Counter(tokens)
    total = len(tokens)
    scores = {}
    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = 0.0
        for kw in keywords:
            kw_parts = [p for p in kw.split() if p not in STOPWORDS]
            if not kw_parts:
                continue
            if len(kw_parts) == 1:
                score += token_counts.get(kw_parts[0], 0)
            elif kw in " ".join(tokens):
                score += 2
        scores[subject] = score
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[0][1]
    if top == 0:
        return []
    results = []
    for name, score in ranked[:top_n]:
        if score == 0:
            break
        results.append({
            "subject": name,
            "score": round(score / top, 3),
            "matches": int(score),
        })
    return results


# ── Keyword extraction (TF-IDF vs. document corpus) ───────────────────────────

def extract_keywords(
    text: str,
    corpus: Optional[List[str]] = None,
    top_n: int = 10,
) -> List[Dict]:
    """Extract the most salient terms using TF-IDF (or pure TF when no corpus)."""
    tokens = _tokenize(text)
    if not tokens:
        return []
    tf = Counter(tokens)
    doc_freq: Counter = Counter()
    if corpus:
        for doc in corpus:
            doc_freq.update(set(_tokenize(doc)))
    num_docs = max(1, len(corpus)) if corpus else 1
    scores = {}
    for token, freq in tf.items():
        if corpus:
            idf = math.log((num_docs + 1) / (doc_freq.get(token, 0) + 1)) + 1.0
        else:
            idf = 1.0
        scores[token] = freq * idf
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    max_score = ranked[0][1] if ranked else 1.0
    return [
        {"keyword": token, "score": round(score / max_score, 3), "frequency": tf[token]}
        for token, score in ranked
    ]


# ── Difficulty ────────────────────────────────────────────────────────────────

def estimate_difficulty(fk_grade: float, ari: float, word_count: int) -> Dict:
    """Combine readability + density into a 1-5 difficulty rating."""
    level = (fk_grade + ari) / 2.0
    if level >= 14:
        difficulty = 5
    elif level >= 11:
        difficulty = 4
    elif level >= 8:
        difficulty = 3
    elif level >= 5:
        difficulty = 2
    else:
        difficulty = 1
    label = {1: "basic", 2: "easy", 3: "medium", 4: "hard", 5: "advanced"}[difficulty]
    return {
        "difficulty": difficulty,
        "difficulty_label": label,
        "readability_grade": round(level, 1),
    }


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyze_document(
    text: str,
    corpus: Optional[List[str]] = None,
    keyword_count: int = 10,
    include_keywords: bool = True,
) -> Dict:
    """Full ML analysis of a document's extracted text (pure scikit-learn-free
    stats + TF-IDF flavored NLP — no external API calls, works offline)."""
    text = (text or "").strip()
    if not text:
        return {"status": "empty", "message": "No text available for analysis."}

    words = _count_words(text)
    sentences = _count_sentences(text)
    tokens = _tokenize(text)
    unique = len(set(tokens))
    fk = _flesch_kincaid(text)
    ari = _automated_readability_index(text)
    reading_minutes = round(words / 200.0, 1)
    diff = estimate_difficulty(fk["flesch_kincaid_grade"], ari, words)

    result = {
        "status": "complete",
        "statistics": {
            "word_count": words,
            "sentence_count": sentences,
            "unique_words": unique,
            "vocabulary_richness": round(unique / words, 3),
            "estimated_reading_minutes": reading_minutes,
            "average_words_per_sentence": round(words / sentences, 1),
        },
        "readability": {
            "flesch_reading_ease": fk["flesch_reading_ease"],
            "flesch_kincaid_grade": fk["flesch_kincaid_grade"],
            "automated_readability_index": ari,
        },
        "difficulty": diff,
        "subject_matches": classify_subject(tokens),
        "topics": [],
    }
    if include_keywords:
        result["keywords"] = extract_keywords(text, corpus=corpus, top_n=keyword_count)
    return result


def find_similar_documents(
    text: str,
    candidates: List[Dict],
    top_n: int = 5,
    min_similarity: float = 0.05,
) -> List[Dict]:
    """Rank other documents by TF-IDF cosine similarity to this one.
    `candidates` = [{"id": ..., "title": ..., "text": ...}]."""
    if not candidates:
        return []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer

        corpus_docs = [c.get("text", "") or "" for c in candidates]
        corpus_docs.append(text)
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            token_pattern=r"[a-zA-Z]{3,}",
            max_features=20000,
        )
        matrix = vectorizer.fit_transform(corpus_docs)
        query_vec = matrix[-1]
        results = []
        for idx, cand in enumerate(candidates):
            sim = float((query_vec.dot(matrix[idx].T)).toarray()[0][0]) if (query_vec.nnz and matrix[idx].nnz) else 0.0
            results.append({
                "file_id": cand.get("id"),
                "title": cand.get("title", "Untitled"),
                "similarity": round(sim, 3),
                "file_type": cand.get("file_type"),
                "pages": cand.get("pages", 0),
                "subject": cand.get("subject"),
            })
        results = [r for r in results if r["similarity"] >= min_similarity]
        results.sort(key=lambda r: r["similarity"], reverse=True)
        return results[:top_n]
    except Exception as e:
        logger.warning(f"Similarity computation failed: {e}")
        return []


ml_analyzer = analyze_document
