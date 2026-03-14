# Consciousness / Path-Dependency Experiment

Demonstrates that a large language model (Mistral via Ollama) has **no internal
workspace**: it cannot truly "hold" a secret number in memory between turns.

## Hypothesis

At temperature = 0, the model is deterministic. If it had a fixed internal state,
the same number would be revealed regardless of which yes/no questions were asked.
Instead, the revealed number is **path-dependent** — it is constructed on-the-fly
from the token history, not retrieved from a stable hidden state.

## Files

| File | Purpose |
|------|---------|
| `main.py` | Runs two question paths that funnel toward opposite ends of [1, 100] and shows the model gives inconsistent or divergent answers. |
| `test_determinism.py` | Verifies T=0 really is deterministic by running each path twice and checking all replies are byte-identical. This rules out randomness as the cause of path-dependency. |

## Setup

```bash
pip install -r requirements.txt
ollama pull mistral
```

## Run

```bash
# Main experiment — shows path-dependency
python3 main.py

# Determinism check — confirms T=0 removes randomness
python3 test_determinism.py
```

## Interpretation

- If `main.py` reveals **different numbers** across paths → path-dependency confirmed.
- If a path reveals a number **outside its implied Yes/No range** → the model
  contradicts itself, proving the answer was generated post-hoc.
- If `test_determinism.py` passes → randomness is not the explanation; the
  divergence is purely a function of conversational context.
