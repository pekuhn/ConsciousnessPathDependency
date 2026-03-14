"""
Determinism Test — Mistral at T=0
==================================
Verifies that ollama/mistral at temperature=0 is truly deterministic:
the exact same question sequence must produce the exact same answers
on every run. Each path is run twice and the transcripts are compared.
"""

import ollama
from main import MODEL, TEMPERATURE, SYSTEM_PROMPT, PATH_A, PATH_B


def run_path(questions: list[str]) -> list[str]:
    """Return the list of raw model replies for a given question sequence."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    seed = (
        "I am going to ask you yes/no questions about a secret number you have chosen "
        "between 1 and 100. Remember your number and stay consistent."
    )
    messages.append({"role": "user", "content": seed})
    resp = ollama.chat(model=MODEL, messages=messages, options={"temperature": TEMPERATURE})
    reply = resp["message"]["content"].strip()
    messages.append({"role": "assistant", "content": reply})

    answers = [reply]  # include seed reply so full output is compared
    for q in questions:
        messages.append({"role": "user", "content": q})
        resp = ollama.chat(model=MODEL, messages=messages, options={"temperature": TEMPERATURE})
        answer = resp["message"]["content"].strip()
        messages.append({"role": "assistant", "content": answer})
        answers.append(answer)

    messages.append({"role": "user", "content": "Please reveal your number now. Reply with ONLY the number."})
    resp = ollama.chat(model=MODEL, messages=messages, options={"temperature": TEMPERATURE})
    answers.append(resp["message"]["content"].strip())
    return answers


def compare(label: str, questions: list[str], runs: int = 2):
    print(f"\n{'='*60}")
    print(f"  {label}  ({runs} runs)")
    print(f"{'='*60}")

    all_runs = [run_path(questions) for _ in range(runs)]
    labels = ["seed"] + [f"Q{i+1}" for i in range(len(questions))] + ["reveal"]

    deterministic = True
    for i, (turn_label, *replies) in enumerate(zip(labels, *[r for r in all_runs])):
        # replies is a list of one reply per run at this turn position
        unique = set(replies)
        match = "OK" if len(unique) == 1 else "MISMATCH"
        if len(unique) > 1:
            deterministic = False
        print(f"  [{match}] {turn_label:8s}: ", end="")
        if len(unique) == 1:
            print(repr(replies[0]))
        else:
            for run_idx, r in enumerate(replies):
                print(f"\n    run {run_idx+1}: {repr(r)}", end="")
            print()

    print()
    print(f"  Result: {'DETERMINISTIC ✓' if deterministic else 'NON-DETERMINISTIC ✗'}")
    print(f"{'='*60}")
    return deterministic


if __name__ == "__main__":
    print("\nDeterminism test — T=0, model=mistral")
    print("Each path is run twice; all replies must be byte-identical.\n")

    ok_a = compare("PATH A  (funnel HIGH)", PATH_A)
    ok_b = compare("PATH B  (funnel LOW) ", PATH_B)

    print("\nOVERALL")
    print("-------")
    if ok_a and ok_b:
        print("  Both paths are deterministic at T=0.")
        print("  Path-dependency in main.py is therefore NOT due to randomness —")
        print("  it is purely a function of conversation context (token history).")
    else:
        print("  At least one path is non-deterministic even at T=0.")
        print("  This may indicate sampling noise in the ollama/mistral backend.")
