# Laya Decision Lab

A local proof of concept accompanying **Untitled slide.pdf**, George Michelon's presentation about Laya (October 2026). It implements the ticket triage example from slide 8 with real inference, without canned responses. The interface is in English to match the slides; sample tickets are available in English and Portuguese.

## Run on macOS

Open `start.command` in Terminal, or run:

```bash
git clone https://github.com/geomichelon/laya-decision-lab.git
cd laya-decision-lab
bash start.command
```

Visit **http://127.0.0.1:8765**. Keep Terminal open; press Ctrl+C to stop. If the PoC is already using the port, use the existing instance. On the first run, the launcher prepares an isolated environment at `~/Library/Application Support/LayaDecisionLab/venv` on macOS (on the internal drive), or `.venv` on Linux. Python 3.11 is recommended; exact dependencies are listed in `requirements.lock.txt`. This PoC is independent of Archmazing.

The model runs locally using PyTorch/MPS (Metal) when available, or CPU. To select CPU explicitly, use `LAYA_LAB_DEVICE=cpu bash start.command`. Public weights are downloaded from Hugging Face on first use; no API key is required. The cache is stored in `.cache/huggingface`; checkpoints and the Python environment are excluded from Git. Two checkpoints are used: `typed-decisions` for English and `multilingual` for Portuguese. Only one is kept in memory at a time; switching languages requires loading the other checkpoint.

Before presenting, run all eight samples to download both checkpoints. Once dependencies and weights are available, you can start with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash start.command`. Initial loading and inference may take longer. Keep the cache for the demonstration.

## Demo walkthrough (3–5 minutes)

1. After slide 7, open the PoC and click **Present** for fullscreen mode. Slide 8 provides the visual introduction.
2. In **Live demo**, choose **Duplicate charge**, then **Analyze ticket**. Show the department (`choice`), urgency distribution (`score`), and probability of cancellation intent (`noul`). These are real results and may differ from the illustrative values in the PDF.
3. Explain **Policy outcome**: a deterministic rule applied to the predictions, rather than another generated response. No refunds or cancellations are executed.
4. Try **The negation test**, followed by a custom ticket. The model can be wrong even with high confidence. Include examples that expose its limitations.
5. Open **Decision schema** to show the questions and criteria sent to the model. The urgency label is the most likely level; the decimal value is the expected ordinal value.
6. In **Evaluate samples**, run all eight cases. Show correct and incorrect predictions for each ticket, department accuracy against expected labels, the rules baseline, and measured latency. Export the JSON for review.
7. Return to the presentation: this demonstrates integration and behavior, while adoption still requires representative data, calibration, and independent evaluation.

## Presentation review

The nine slides connect the project's origins, architecture, usage, alternatives, and pilot. Slide 8 defines a suitable PoC scope; slide 9 only checks whether the package can be imported. The demonstration also covers model loading, inference, and the interface.

The main narrative improvement is to distinguish **prediction**, **confidence**, and **policy**. A structured output can still be semantically wrong. The official documentation describes sensitivity to labels and negation, as well as the need for domain evaluation and calibration. This demo therefore does not present confidence as measured accuracy.

Slide 7 proposes a full comparison with Jev, LLMs, and rules. This version implements **Laya versus rules for department classification**. It does not integrate Jev or an LLM, measure financial costs, or compare latency with external APIs. Eight visible synthetic tickets are not an independent test set. These results should not be used as a market benchmark or evidence of superiority.

When updating the slides, replace “No live inference” on slide 8 with a reference to the live demo. Keep the numbers labeled as examples, or use an exported result with hardware, version, and date details. Add sources to slide 2 and the technical limitations. The public repository is [geomichelon/laya-decision-lab](https://github.com/geomichelon/laya-decision-lab). The original PDF was preserved and is not included in this repository.

## Implementation and limitations

- FastAPI backend; HTML/CSS/JavaScript frontend without CDNs. The server binds to `127.0.0.1`.
- Laya 0.4.15, using `convaiinnovations/laya` weights pinned to revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`.
- Questions are defined in `questions.json`. Expected labels in `samples.json` are used only for evaluation and are not sent to the model.
- The policy suggests human review if any confidence is below the threshold, cancellation probability is at least 0.5, or expected urgency is at least 1.5. The default 80% confidence threshold is illustrative and has not been calibrated for this domain. The policy never executes actions.
- Inference latency includes the local SDK call and GPU synchronization. It excludes downloads, model loading, and HTTP overhead; total server time is reported separately. Sample p95 uses the nearest-rank method and includes the first inference after loading each model. It is not a production performance guarantee.
- Baseline: ordered keyword rules for Billing, Technical, Sales, and Other. It compares department classification only and does not understand negation or context.
- Input is limited to 2,000 characters and 450 checkpoint tokens to reduce truncation risk. Errors are not replaced with simulated responses. Inference is serialized; concurrent requests receive HTTP 409.
- Custom ticket text is neither saved to disk nor sent to an inference API. Exports are saved only when the user downloads the JSON. Artifacts in `evidence/` contain synthetic tickets only.

## Tests

```bash
"$HOME/Library/Application Support/LayaDecisionLab/venv/bin/python" -m unittest discover -s tests -v
```

Three tests cover policy boundaries, a single low-confidence output, invalid input, and allowed origins and hosts. Chromium checks covered real inference, JSON export, clearing results after edits, the schema, all eight samples, Portuguese input, and a 390 px viewport without horizontal overflow.

The real evaluation on October 25, 2026 produced **7/8 correct departments (87.5%)**, compared with 8/8 for rules; cancellation classification was correct in 6/8 cases (75%), and urgency mean absolute error was 0.569 on a 0–2 scale. The initial evaluation measured p50 = 119.55 ms and p95 = 498.34 ms; the final offline retest measured p50 = 114.14 ms and p95 = 142.69 ms across eight inferences, excluding model loading. The illustrative 80% threshold sent every case to human review. The first request in the initial session took 2,715 ms; warmup and Mac workload affect latency. The Portuguese pricing request was incorrectly classified as Billing. The English outage case produced a false positive for cancellation intent. These results do not demonstrate an advantage over rules on this sample set.

Inference and browser evidence is available in `evidence/`, including responses, schema and revision details, latencies, and screenshots. Inference responses are real. These results should not be extrapolated to production.

To repeat the browser checks while the server is running:

```bash
npm install
npx playwright install chromium
npm run test:browser
```

The browser test runs real local inference and overwrites only synthetic-ticket evidence in `evidence/`. The complete retest also passed with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` after both checkpoints had been downloaded. An early test exposed a brief window where the analysis button was enabled before model status had been fetched; UI initialization now waits for model status.

## Docker (alternative distribution)

The Dockerfile is provided but has not been validated in this delivery, which uses native MPS on macOS. Docker Desktop runs this workload on CPU, without direct access to the host's MPS device.

```bash
docker build -t laya-decision-lab .
docker run --rm -p 127.0.0.1:8765:8765 -v laya-models:/models laya-decision-lab
```

## Sources

- [Official Laya source and limitations](https://github.com/NandhaKishorM/laya)
- [Question and answer types](https://github.com/NandhaKishorM/laya/blob/main/docs/questions-and-answers.md)
- [Python distribution](https://pypi.org/project/laya/)
- [Public model weights](https://huggingface.co/convaiinnovations/laya)
