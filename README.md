# Laya Decision Lab

A local proof of concept accompanying **Untitled slide.pdf**, George Michelon's presentation about Laya (October 2026). It implements the ticket triage example from slide 8 with real inference, without canned responses. The interface is in English to match the slides; sample tickets are available in English and Portuguese.

For an isolated installation, follow [Run with Docker](#run-with-docker). To use Metal acceleration directly on your Mac, use the native launcher below.

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
npm ci
npx playwright install chromium
npm run test:browser
```

The browser test runs real local inference and overwrites only synthetic-ticket evidence in `evidence/`. The complete retest also passed with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` after both checkpoints had been downloaded. An early test exposed a brief window where the analysis button was enabled before model status had been fetched; UI initialization now waits for model status.

## Run with Docker

This option requires **Docker Desktop** (with its engine running) and Git. Python and Node.js do not need to be installed on the host to run the demo. Node.js is only needed for the optional browser tests.

```bash
git clone https://github.com/geomichelon/laya-decision-lab.git
cd laya-decision-lab
docker compose up --build -d
```

Open **http://127.0.0.1:8765** and wait for **Local model ready** before analyzing a ticket. The first build installs the Python dependencies; the first startup downloads the English checkpoint. Selecting a Portuguese sample downloads the multilingual checkpoint on first use. Internet access is required for these initial downloads, but no API key is needed.

The Compose configuration uses the CPU build of PyTorch. On macOS, Docker does not use Metal; the native launcher is available when you want MPS acceleration. Downloads and model loading are separate from the inference latency shown in the interface. The app is exposed only on the local machine.

If port 8765 is already in use, choose another host port:

```bash
LAYA_PORT=8766 docker compose up --build -d
```

Then open **http://127.0.0.1:8766**. Use the same `LAYA_PORT` value when recreating the service. On PowerShell, set `$env:LAYA_PORT="8766"` before running the Compose command. Windows execution has not been tested in this delivery.

Check startup progress and model readiness:

```bash
docker compose logs -f demo
docker compose ps
```

`health: starting` is expected during the first download. `healthy` means the model is ready or processing a request. Press Ctrl+C to stop following logs; this does not stop the container. If the interface reports a loading error, inspect the logs and check the connection to Hugging Face.

Stop the demo:

```bash
docker compose down
```

Model downloads are kept in the named Docker volume `laya-decision-lab_models`, including across container recreation. Running `docker compose down` preserves that volume; adding `-v` deletes it and requires downloading the models again. The Docker volume is separate from the native launcher's `.cache/huggingface` directory.

After running all eight samples to cache both checkpoints, recreate the service in offline mode:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 docker compose up -d --no-build --force-recreate
```

If using the alternate port, prepend `LAYA_PORT=8766` to that command. To return to online mode, recreate with both offline variables set to `0`. Offline mode requires the image and both checkpoints to have been downloaded first.

To repeat the browser checks against Docker without replacing the native-run evidence:

```bash
npm ci
npx playwright install chromium
BASE_URL=http://127.0.0.1:8765 EVIDENCE_DIR=evidence/docker npm run test:browser
```

Use port 8766 in `BASE_URL` if that is where the container is running. These checks execute real local inference, including all eight samples.

### Docker validation

Validated on October 25, 2026 with Docker Desktop 4.42.1, Engine 28.2.2, and Compose 2.37.1 on Apple Silicon (`linux/arm64`), with 8 CPUs and approximately 7.65 GiB allocated to Docker. The image uses PyTorch `2.14.1+cpu` without CUDA libraries and is approximately 1.17 GB before model downloads. Windows and `linux/amd64` have not been validated.

- A clean build and first startup with a new model volume passed. Downloading and loading the English checkpoint took approximately 33 seconds on this connection.
- All three Python tests passed inside the image.
- Chromium checks passed for real inference, JSON export, editing, the schema, all eight samples, Portuguese, and desktop/mobile layouts. All eight inference requests succeeded; department accuracy remained 7/8, compared with 8/8 for the rules baseline.
- Docker/CPU inference latency across the eight samples was p50 = 1,231.49 ms and p95 = 1,391.98 ms, excluding downloads and loading. These measurements are separate from the native Metal results above.
- Both checkpoints produced real results in a new container with `--network none`, using the persisted model volume.
- Recreating the Compose service with offline mode enabled returned it to `healthy`; a subsequent real HTTP inference also passed.

Evidence is in [`evidence/docker/validation.json`](evidence/docker/validation.json), with browser screenshots and exported predictions in the same directory. The SDK emitted a checkpoint-temperature warning; confidence remains uncalibrated and the review threshold remains illustrative.

To repeat the network-isolated check after both models have been cached:

```bash
docker run --rm -i --network none -v laya-decision-lab_models:/models laya-decision-lab:local python - < tests/docker_offline.py
```

## Sources

- [Official Laya source and limitations](https://github.com/NandhaKishorM/laya)
- [Question and answer types](https://github.com/NandhaKishorM/laya/blob/main/docs/questions-and-answers.md)
- [Python distribution](https://pypi.org/project/laya/)
- [Public model weights](https://huggingface.co/convaiinnovations/laya)

- [Official PyTorch CPU installation instructions](https://pytorch.org/get-started/locally/)
