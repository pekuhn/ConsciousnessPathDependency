"""
Consciousness / Path-Dependency Experiment
==========================================
Hypothesis: an LLM at T=0 has NO internal workspace.
When asked to "think of a number", the number is not fixed —
it is constructed on-the-fly from the conversation history.
Therefore the final revealed number is PATH-DEPENDENT on
which yes/no questions were asked first.

We run the same opening prompt with two different question
paths and show the revealed number differs (or is forced into
inconsistency), proving there is no stable hidden state.
"""

import ollama

MODEL = "mistral"
TEMPERATURE = 0.0

SYSTEM_PROMPT = (
    "You are playing a guessing game. "
    "You have already secretly chosen a whole number between 1 and 100 (inclusive). "
    "Do NOT reveal the number until explicitly asked. "
    "Answer every yes/no question about your number with ONLY 'Yes' or 'No'. "
    "Never change your number. Be consistent."
)

# ---------------------------------------------------------------------------
# Two question paths that "funnel" toward different regions of [1,100]
# ---------------------------------------------------------------------------
PATH_A = [
    "Is your number greater than 50?",
    "Is your number greater than 75?",
    "Is your number greater than 87?",
    "Is your number even?",
]

PATH_B = [
    "Is your number less than or equal to 50?",
    "Is your number less than or equal to 25?",
    "Is your number less than or equal to 12?",
    "Is your number odd?",
]


def chat(messages: list[dict]) -> str:
    resp = ollama.chat(model=MODEL, messages=messages, options={"temperature": TEMPERATURE})
    return resp["message"]["content"].strip()


def run_trial(path_label: str, questions: list[str]) -> dict:
    """Play one full round, printing every turn live, and return the transcript."""
    print(f"\n{'='*60}")
    print(f"  PATH {path_label}")
    print(f"{'='*60}")
    print(f"  [SYSTEM] {SYSTEM_PROMPT}\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Seed: ask the model to commit
    seed_prompt = (
        "I am going to ask you yes/no questions about a secret number you have chosen "
        "between 1 and 100. Remember your number and stay consistent."
    )
    print(f"  [USER]      {seed_prompt}")
    messages.append({"role": "user", "content": seed_prompt})
    seed_reply = chat(messages)
    messages.append({"role": "assistant", "content": seed_reply})
    print(f"  [MISTRAL]   {seed_reply}\n")

    transcript = []

    # Ask the path-specific questions
    for q in questions:
        print(f"  [USER]      {q}")
        messages.append({"role": "user", "content": q})
        answer = chat(messages)
        messages.append({"role": "assistant", "content": answer})
        transcript.append({"question": q, "answer": answer})
        print(f"  [MISTRAL]   {answer}")

    # Reveal
    reveal_prompt = "Please reveal your number now. Reply with ONLY the number."
    print(f"\n  [USER]      {reveal_prompt}")
    messages.append({"role": "user", "content": reveal_prompt})
    revealed = chat(messages)
    print(f"  [MISTRAL]   {revealed}")

    # Consistency check: derive the implied range from Yes/No answers
    lo, hi = 1, 100
    for item in transcript:
        q = item["question"].lower()
        a = item["answer"].lower().startswith("y")
        if "greater than" in q:
            n = int("".join(filter(str.isdigit, q)))
            if a:
                lo = max(lo, n + 1)
            else:
                hi = min(hi, n)
        elif "less than or equal to" in q:
            n = int("".join(filter(str.isdigit, q)))
            if a:
                hi = min(hi, n)
            else:
                lo = max(lo, n + 1)

    try:
        revealed_int = int("".join(filter(str.isdigit, revealed)))
    except ValueError:
        revealed_int = None

    consistent = (revealed_int is not None) and (lo <= revealed_int <= hi)

    return {
        "path": path_label,
        "seed_reply": seed_reply,
        "transcript": transcript,
        "implied_range": (lo, hi),
        "revealed": revealed,
        "revealed_int": revealed_int,
        "consistent": consistent,
    }


def print_result(r: dict):
    lo, hi = r["implied_range"]
    print(f"\n  --> Implied range from Yes/No answers : [{lo}, {hi}]")
    print(f"  --> Revealed number                   : {r['revealed']}")
    print(f"  --> Internally consistent              : {'YES ✓' if r['consistent'] else 'NO  ✗  <-- PATH DEPENDENCY EXPOSED'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("\nRunning experiment: T=0, model=mistral")
    print("Hypothesis: final number is path-dependent (no internal workspace)")

    result_a = run_trial("A  (funnel HIGH: >50 >75 >87)", PATH_A)
    print_result(result_a)

    result_b = run_trial("B  (funnel LOW:  ≤50 ≤25 ≤12)", PATH_B)
    print_result(result_b)

    # Summary verdict
    ra = result_a["revealed_int"]
    rb = result_b["revealed_int"]
    print("SUMMARY")
    print("-------")
    print(f"  Path A revealed : {ra}  (questions funnelled toward 88-100)")
    print(f"  Path B revealed : {rb}  (questions funnelled toward 1-12)")

    if ra != rb:
        print(f"\n  Numbers DIFFER ({ra} vs {rb}).")
        print("  The LLM's 'secret number' changed depending on which questions")
        print("  were asked — it has NO fixed internal workspace.")
    else:
        print(f"\n  Numbers happen to match ({ra}), but check consistency flags above.")
        print("  Even if equal by chance, an inconsistent Yes/No trail reveals")
        print("  the answer was constructed post-hoc, not stored a priori.")

    if not result_a["consistent"] or not result_b["consistent"]:
        print("\n  At least one path produced an INCONSISTENT answer —")
        print("  the revealed number contradicts the model's own Yes/No replies,")
        print("  which is only possible if no number was ever truly 'held'.")
