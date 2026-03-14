"""
Consciousness / Path-Dependency Experiment — Claude via Anthropic API
======================================================================
Same experiment as main.py but using claude-opus-4-6 at temperature=0
instead of Mistral via Ollama.

Requires:
    export ANTHROPIC_API_KEY=sk-ant-...
    pip install anthropic
"""

import anthropic
from main import PATH_A, PATH_B

MODEL = "claude-opus-4-6"
TEMPERATURE = 0.0

SYSTEM_PROMPT = (
    "You are playing a guessing game. "
    "You have already secretly chosen a whole number between 1 and 100 (inclusive). "
    "Do NOT reveal the number until explicitly asked. "
    "Answer every yes/no question about your number with ONLY 'Yes' or 'No'. "
    "Never change your number. Be consistent."
)

client = anthropic.Anthropic()


def chat(messages: list[dict]) -> str:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=256,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return next(b.text for b in resp.content if b.type == "text").strip()


def run_trial(path_label: str, questions: list[str]) -> dict:
    """Play one full round, printing every turn live."""
    print(f"\n{'='*60}")
    print(f"  PATH {path_label}")
    print(f"{'='*60}")
    print(f"  [SYSTEM] {SYSTEM_PROMPT}\n")

    messages = []

    seed_prompt = (
        "I am going to ask you yes/no questions about a secret number you have chosen "
        "between 1 and 100. Remember your number and stay consistent."
    )
    print(f"  [USER]    {seed_prompt}")
    messages.append({"role": "user", "content": seed_prompt})
    seed_reply = chat(messages)
    messages.append({"role": "assistant", "content": seed_reply})
    print(f"  [CLAUDE]  {seed_reply}\n")

    transcript = []
    for q in questions:
        print(f"  [USER]    {q}")
        messages.append({"role": "user", "content": q})
        answer = chat(messages)
        messages.append({"role": "assistant", "content": answer})
        transcript.append({"question": q, "answer": answer})
        print(f"  [CLAUDE]  {answer}")

    reveal_prompt = "Please reveal your number now. Reply with ONLY the number."
    print(f"\n  [USER]    {reveal_prompt}")
    messages.append({"role": "user", "content": reveal_prompt})
    revealed = chat(messages)
    print(f"  [CLAUDE]  {revealed}")

    # Consistency check
    lo, hi = 1, 100
    for item in transcript:
        q = item["question"].lower()
        a = item["answer"].lower().startswith("y")
        if "greater than" in q:
            n = int("".join(filter(str.isdigit, q)))
            lo, hi = (max(lo, n + 1), hi) if a else (lo, min(hi, n))
        elif "less than or equal to" in q:
            n = int("".join(filter(str.isdigit, q)))
            lo, hi = (lo, min(hi, n)) if a else (max(lo, n + 1), hi)

    try:
        revealed_int = int("".join(filter(str.isdigit, revealed)))
    except ValueError:
        revealed_int = None

    consistent = (revealed_int is not None) and (lo <= revealed_int <= hi)

    print(f"\n  --> Implied range from Yes/No answers : [{lo}, {hi}]")
    print(f"  --> Revealed number                   : {revealed}")
    print(f"  --> Internally consistent              : {'YES ✓' if consistent else 'NO  ✗  <-- PATH DEPENDENCY EXPOSED'}")
    print(f"{'='*60}")

    return {
        "path": path_label,
        "implied_range": (lo, hi),
        "revealed": revealed,
        "revealed_int": revealed_int,
        "consistent": consistent,
    }


if __name__ == "__main__":
    print(f"\nRunning experiment: T=0, model={MODEL}")
    print("Hypothesis: final number is path-dependent (no internal workspace)")

    result_a = run_trial("A  (funnel HIGH: >50 >75 >87)", PATH_A)
    result_b = run_trial("B  (funnel LOW:  ≤50 ≤25 ≤12)", PATH_B)

    ra = result_a["revealed_int"]
    rb = result_b["revealed_int"]

    print("\nSUMMARY")
    print("-------")
    print(f"  Path A revealed : {ra}  (questions funnelled toward 88-100)")
    print(f"  Path B revealed : {rb}  (questions funnelled toward 1-12)")

    if ra != rb:
        print(f"\n  Numbers DIFFER ({ra} vs {rb}).")
        print("  The LLM's 'secret number' changed depending on which questions")
        print("  were asked — it has NO fixed internal workspace.")
    else:
        print(f"\n  Numbers happen to match ({ra}), but check consistency flags above.")

    if not result_a["consistent"] or not result_b["consistent"]:
        print("\n  At least one path produced an INCONSISTENT answer —")
        print("  the revealed number contradicts the model's own Yes/No replies.")
