import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import ollama

# -----------------------------
# Embedding Model
# -----------------------------
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
model = SentenceTransformer(EMBEDDING_MODEL)

# -----------------------------
# Embedding helper
# -----------------------------
def get_embeddings(texts):
    return model.encode(texts, normalize_embeddings=True)

# -----------------------------
# Semantic similarity
# -----------------------------
def semantic_similarity(ref_emb, stu_emb):
    return float(cosine_similarity([ref_emb], [stu_emb])[0][0])

# -----------------------------
# Entailment proxy (hybrid approximation)
# -----------------------------
def entailment_score(reference: str, student: str):
    ref_emb, stu_emb = get_embeddings([reference, student])

    ref_to_stu = cosine_similarity([ref_emb], [stu_emb])[0][0]
    stu_to_ref = cosine_similarity([stu_emb], [ref_emb])[0][0]

    symmetry_gap = abs(ref_to_stu - stu_to_ref)

    entailment = (0.7 * ref_to_stu) + (0.3 * (1 - symmetry_gap))

    return float(np.clip(entailment, 0.0, 1.0))

# -----------------------------
# Keyword overlap (light signal)
# -----------------------------
def keyword_overlap(reference: str, student: str):
    ref_words = set(reference.lower().split())
    stu_words = set(student.lower().split())

    if not ref_words:
        return 0.0

    return len(ref_words & stu_words) / len(ref_words)

# -----------------------------
# Length ratio
# -----------------------------
def length_ratio(reference: str, student: str):
    ref_len = max(len(reference.split()), 1)
    stu_len = len(student.split())

    return min(stu_len / ref_len, 1.0)

# -----------------------------
# Rubric evaluation
# -----------------------------
def evaluate_rubric(reference: str, student: str):
    ref_emb, stu_emb = get_embeddings([reference, student])

    semantic = semantic_similarity(ref_emb, stu_emb)
    entailment = entailment_score(reference, student)
    overlap = keyword_overlap(reference, student)
    length = length_ratio(reference, student)

    rubric = {
        "conceptual_understanding": (0.5 * semantic + 0.5 * entailment),
        "key_points_coverage": entailment * (0.6 + 0.4 * overlap),
        "clarity_and_structure": (0.5 * overlap + 0.5 * length),
        "completeness": entailment * semantic,
        "precision": (0.7 * entailment + 0.3 * semantic)
    }

    return rubric

# -----------------------------
# Final score
# -----------------------------
def compute_final_score(rubric):
    weights = {
        "conceptual_understanding": 0.35,
        "key_points_coverage": 0.25,
        "clarity_and_structure": 0.15,
        "completeness": 0.15,
        "precision": 0.10
    }

    score = sum(rubric[k] * w for k, w in weights.items())
    return float(np.clip(score, 0.0, 1.0))

# -----------------------------
# LLM-based Generative Feedback (Llama 3.2:1B via Ollama)
# -----------------------------
def generate_llm_feedback(question, reference, student, rubric):
    weaknesses = []

    if rubric["conceptual_understanding"] < 0.6:
        weaknesses.append("Weak conceptual understanding")
    if rubric["key_points_coverage"] < 0.6:
        weaknesses.append("Missing key points")
    if rubric["clarity_and_structure"] < 0.6:
        weaknesses.append("Poor clarity/structure")
    if rubric["precision"] < 0.6:
        weaknesses.append("Low precision in explanations")
    if rubric["completeness"] < 0.6:
        weaknesses.append("Incomplete answer")

    prompt = f"""
You are an expert academic examiner.

TASK:
Evaluate the student's answer and provide clear, constructive feedback.

QUESTION:
{question}

REFERENCE ANSWER:
{reference}

STUDENT ANSWER:
{student}

RUBRIC SCORES:
{rubric}

WEAK AREAS:
{weaknesses}

INSTRUCTIONS:
- Be strict but fair
- Focus on improvement points
- Mention strengths briefly if present
- Keep response concise (5–8 lines)
- Do NOT restate the rubric numbers
"""

    response = ollama.chat(
        model="llama3.2:1b",
        messages=[
            {
                "role": "system",
                "content": "You are a strict academic examiner who gives clear and structured feedback."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0.6
        }
    )

    return response["message"]["content"]

# -----------------------------
# Public API
# -----------------------------
def grade_answer(reference: str, student: str, question: str = ""):
    rubric = evaluate_rubric(reference, student)
    score = compute_final_score(rubric)

    feedback = generate_llm_feedback(
        question=question,
        reference=reference,
        student=student,
        rubric=rubric
    )

    return {
        "score": score,
        "rubric": rubric,
        "feedback": feedback
    }