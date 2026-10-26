# Laya Decision Lab

A local, interactive ticket-triage demonstration with real Laya inference. The interface and documentation are in English; the 16 synthetic examples include English and Portuguese. The app never refunds, cancels subscriptions, routes real tickets or contacts customers.

**For presenting:** open the **Presenter guide** tab and read [the speaker notes](PRESENTATION.md). The central idea is: **Laya predicts signals; your policy determines the proposed workflow.**

## Run natively on macOS

Python 3.11 is recommended. Clone the repository, then run:

```bash
git clone https://github.com/geomichelon/laya-decision-lab.git
cd laya-decision-lab
bash start.command
```

Open **http://127.0.0.1:8765** and wait for **Local model ready**. Keep Terminal open; Ctrl+C stops the server. The launcher installs the locked dependencies into `~/Library/Application Support/LayaDecisionLab/venv` on macOS, or `.venv` on Linux. Native Linux execution has not been validated.

PyTorch uses Metal (MPS) when available, otherwise CPU. To force CPU: `LAYA_LAB_DEVICE=cpu bash start.command`. Public model weights are downloaded from Hugging Face without a key and stored in `.cache/huggingface`. English uses `typed-decisions`; Portuguese uses `multilingual`. Only one checkpoint stays resident, so changing languages includes loading time. Run both languages before presenting. After dependencies and both checkpoints are cached:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash start.command
```

## How this project was created

This standalone application was created for a technical presentation on evaluating Laya for support-ticket triage in a company setting. The first version asked three questions; the current version adds a requested-action question and separates routing from approval. No model was trained or fine-tuned to build this demo.

The implementation followed these steps:

1. Define the input contract in `questions.json`: department, urgency, cancellation intent and requested action, each with explicit criteria.
2. Build a Python FastAPI service to load the checkpoints, validate input and call the real Laya SDK. Uvicorn serves the API and static files on localhost.
3. Keep application policy in `domain.py`, separate from inference. This makes thresholds and approval rules inspectable and allows recalculation without another prediction.
4. Build the interface in plain HTML, CSS and JavaScript. It uses `fetch` to call the API; there is no React, Next.js, frontend bundler or CDN dependency.
5. Add synthetic examples and expected labels in `samples.json`, then test policy behavior with Python `unittest` and the real browser flow with Playwright. Expected labels are used only after inference for comparison.
6. Add a native launcher, locked dependencies, Docker Compose, JSON exports, saved test evidence and a presentation guide.

### Technologies and their roles

| Component | Technology | Purpose |
|---|---|---|
| API and application policy | Python 3.11, FastAPI, Pydantic, Uvicorn | Validate requests, execute inference and apply rules |
| Decision model | Laya SDK 0.4.15 | Return typed decisions from ticket text |
| Model execution | PyTorch; Metal/MPS or CPU | Run the downloaded checkpoints locally |
| Interface | HTML, CSS, JavaScript | Display predictions, policy traces and evaluation results |
| Tests | Python unittest and Playwright | Check rules, API behavior and real desktop/mobile flows |
| Optional packaging | Docker and Compose | Run an isolated CPU environment with persistent model storage |

### Repository structure

```text
laya-decision-lab/
├── app.py                  # FastAPI endpoints and real Laya inference
├── domain.py               # Routing, priority, approval and keyword baseline
├── questions.json          # Four typed questions sent to the model
├── samples.json            # 16 synthetic examples and evaluation labels
├── static/
│   ├── index.html          # Interface and presenter guide
│   ├── app.css             # Responsive layout
│   └── app.js              # API calls, policy controls and evaluation UI
├── tests/
│   ├── test_lab.py         # Policy and API tests
│   ├── browser.cjs         # Real-inference browser checks
│   └── docker_offline.py   # Cached-model checks without network access
├── evidence/               # Synthetic predictions, screenshots and reports
├── requirements.txt        # Top-level dependency declarations
├── requirements.lock.txt   # Exact Python versions used by the launcher
├── package.json            # Optional browser-test dependencies only
├── package-lock.json       # Locked browser-test dependencies
├── start.command           # Native setup and server launcher
├── Dockerfile              # CPU-only container image
├── compose.yaml            # Local port, model volume and health check
├── PRESENTATION.md         # Six-minute walkthrough and speaker notes
└── README.md
```

`POST /api/analyze` runs Laya. `POST /api/policy` only reapplies deterministic rules. `GET /api/config` supplies questions, samples and presets; `GET /api/status` reports model loading/readiness. No database, external inference service or paid API key is required.

## How Laya was installed and downloaded

There are **two separate downloads**: the Python SDK and its dependencies, then the model weights. Installing the package alone does not download or run a checkpoint.

### 1. Install the Python package

The native launcher creates an isolated virtual environment and runs `pip install -r requirements.lock.txt`. That file pins `laya==0.4.15`, `torch==2.14.1`, FastAPI and the other tested dependencies. The smaller `requirements.txt` declares `laya[serve]==0.4.15` and HTTPX, but the launcher uses the exact lock file for reproducibility.

The equivalent manual installation on macOS, from the cloned repository, is:

```bash
laya_venv="$HOME/Library/Application Support/LayaDecisionLab/venv"
python3.11 -m venv --copies "$laya_venv"
"$laya_venv/bin/python" -m pip install -r requirements.lock.txt
"$laya_venv/bin/python" -m pip check
```

Normally, just use `bash start.command`; the manual commands explain the setup it performs. Its lock-file hash prevents reinstalling dependencies on every launch. Docker performs package installation inside the image and explicitly installs the official CPU-only PyTorch wheel before applying the lock file.

### 2. Download the pretrained checkpoints

The application uses the SDK's `laya.load(...)` call to fetch public files from Hugging Face. It does not clone the upstream Laya source repository, use a hosted inference endpoint or train a new model.

| Setting | Value |
|---|---|
| Hugging Face repository | `convaiinnovations/laya` |
| Pinned model revision | `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` |
| English checkpoint subfolder | `typed-decisions` |
| Portuguese checkpoint subfolder | `multilingual` |
| Native download/cache location | `.cache/huggingface` inside this project |
| Docker cache location | `/models`, backed by the `laya-decision-lab_models` volume |
| Authentication | Public downloads with `token=False`; no Hugging Face token required |

The core loading and prediction calls below reproduce the integration used in `app.py`. Run this in the project's Python environment from the repository directory if you want to inspect the SDK directly; stop the demo first to avoid loading another model alongside it.

```python
import json
import os
from pathlib import Path

os.environ["HF_HOME"] = str(Path.cwd() / ".cache" / "huggingface")
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

import laya
import torch

device = "mps" if torch.backends.mps.is_available() else "cpu"
agent = laya.load(
    "convaiinnovations/laya",
    subfolder="typed-decisions",
    revision="55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851",
    device=device,
    token=False,
)
questions = json.loads(Path("questions.json").read_text())
result = agent.predict(
    "Please send a copy of my invoice. There is no rush.",
    questions,
    max_len=1024,
    head_max_len=256,
)
print(json.dumps(result["answers"], indent=2))
```

For the Portuguese checkpoint, change `subfolder` to `"multilingual"` and use a Portuguese ticket. The application makes that selection automatically when a sample is chosen; custom input uses the checkpoint selected in the interface.

On server startup, the demo preloads the English checkpoint in the background. The first Portuguese analysis loads/downloads the multilingual checkpoint. Later requests reuse cached files; only one model is resident at a time. Running **Evaluate samples → Run 16 samples** exercises both checkpoints.

For the pinned revision, cached checkpoint files are located under:

```text
.cache/huggingface/hub/models--convaiinnovations--laya/
└── snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/
    ├── typed-decisions/
    └── multilingual/
```

These directories were verified in the local installation. The virtual environment, model weights, cache and runtime logs are excluded from Git. Someone cloning this repository downloads their own copy on first use. Installing dependencies and fetching weights require internet access initially; after that, the offline commands in this guide reuse the local cache. The Docker validation also ran both checkpoints in a container with `--network none`.

## How the demo works

1. A ticket and the fixed questions in `questions.json` are sent to one local Laya SDK prediction call. Expected sample labels are never sent to the model.
2. Laya returns four signals: department (`choice`), urgency (`score`, 0–2), cancellation intent (`noul`) and requested action (`choice`). They are predictions, not permissions.
3. Deterministic Python rules in `domain.py` produce separate routing, priority and action proposals. The trace explains these rules, not the model's hidden reasoning.
4. Exports retain the inference ID, original inputs, schema version, checkpoint revision, predictions, policy and measured latency. Editing the ticket or checkpoint invalidates the previous result.

### Routing, priority and approval are independent

| Decision | Rule | Meaning |
|---|---|---|
| Team / routing | Department confidence >= selected threshold | Eligible for automatic routing; otherwise review the team assignment. No ticket is actually routed. |
| Priority | Expected urgency >= 1.5 is High; >= 0.5 is Medium; otherwise Low | Low urgency confidence adds a validation flag. Neither urgency nor this flag blocks routing. |
| Refund / cancellation action | Always requires approval when predicted | Confidence cannot waive financial/account approval. |
| Other action | Unclear label or action confidence below threshold requires clarification | Otherwise informational, technical or sales assistance is suggested. No action is executed. |
| Retention | Cancellation probability >= 0.5 | Adds an attention flag without blocking routing. |

The policy can only react to what the model predicts. A missed refund or cancellation is still possible, so these rules are not a production safety guarantee. The demo is a proposal-only system.

### What the threshold means

**Probability** ranks candidate answers. **Confidence** is a separate SDK output, not measured accuracy. Routing uses department confidence, not the minimum confidence across all questions. Low confidence in urgency or action stays visible in its own decision.

Conservative (80%), Balanced (50%) and Exploratory (20%) are **experimental presets**, not calibrated recommendations. The same threshold also flags uncertain priority/action predictions. Changing a preset or the slider calls `/api/policy` with the existing answers. It does not call Laya again; the prediction, inference ID and inference time stay unchanged. The original inference input and current policy threshold are exported separately.

A refund can be eligible for automatic routing to Billing while still requiring human approval. High urgency can raise priority without making the team assignment uncertain.

## The 16 demonstration examples

Choose an example under **Start with an example**, then click **Analyze ticket**. The table shows **expected labels authored for evaluation**, not guaranteed model outputs. Complete ticket texts, urgency labels and cancellation labels are in [`samples.json`](samples.json). The newest eight examples broaden the original refund/outage-heavy set with routine, noisy, ambiguous and negated requests.

| Example / ID | Language | What it illustrates | Expected team | Expected action |
|---|---|---|---|---|
| Duplicate charge (`duplicate`) | EN | Refund request with a conditional cancellation threat | Billing | `refund` |
| Production outage (`outage`) | EN | Blocked work and an urgent technical request | Technical | `technical_help` |
| A future purchase (`pricing`) | EN | Pre-purchase pricing without urgency | Sales | `sales_inquiry` |
| The negation test (`negation`) | EN | Explicitly rejects cancellation and requests an invoice | Billing | `information` |
| A small suggestion (`feedback`) | EN | Non-urgent product feedback | Other | `information` |
| Leaving the service (`cancel`) | EN | Explicit cancellation before renewal | Billing | `cancellation` |
| Duplicate charge in Portuguese (`pt-billing`) | PT | Portuguese refund request with a cancellation threat | Billing | `refund` |
| A new team in Portuguese (`pt-pricing`) | PT | Portuguese pricing and plan inquiry | Sales | `sales_inquiry` |
| Routine invoice copy (`invoice`) | EN | Routine information request, no account changes | Billing | `information` |
| Getting started (`howto`) | EN | Request for a user guide; nothing is broken | Other | `information` |
| Login with typos (`typo`) | EN | Misspellings in an urgent login issue | Technical | `technical_help` |
| Not enough context (`ambiguous`) | EN | Insufficient detail to determine the requested action | Other | `unclear` |
| Two competing requests (`multiple`) | EN | Requests both a refund and cancellation | Billing | `unclear` |
| Routine invoice in Portuguese (`pt-invoice`) | PT | Explicitly rejects cancellation and refund in Portuguese | Billing | `information` |
| No technical keywords (`paraphrase`) | EN | Describes a failure without the baseline keywords | Technical | `technical_help` |
| Refund explicitly declined (`negated-refund`) | EN | Rejects a refund and requests only a receipt | Billing | `information` |

### Three examples to explain live

**Routine invoice copy**

> Please send me a copy of my invoice for September. No changes to my subscription are needed and there is no rush.

Expected: Billing, low urgency, no cancellation intent and an information request. In the recorded run, the model identified the team and action but its urgency score led the policy to propose Medium priority. Change 80% to 20% to show how the same department prediction becomes eligible for routing; changing the threshold does not improve the prediction itself.

**Duplicate charge**

> I was charged twice for March. Please refund the duplicate payment today, or I will cancel my subscription.

Expected: Billing, high urgency, a cancellation signal and a refund request. The action question distinguishes the immediate refund request from the conditional cancellation threat. Even when routing is eligible at 20%, a predicted refund still requires human approval.

**Routine invoice in Portuguese**

> Pode enviar uma cópia da minha fatura de setembro? Não quero cancelar nem pedir estorno. Não tenho urgência.

Expected: Billing, low urgency, no cancellation intent and an information request. In the recorded run the model incorrectly predicted cancellation. Show this example to explain why a correct department and a typed response do not guarantee a correct action.

### Recorded outcomes and policy trade-offs

The final native Metal run on October 26, 2026 completed all 16 requests: **15/16 department labels matched**, compared with **14/16 for keyword rules**; **12/16 requested-action labels matched**. With either the 80% or 50% routing threshold, 2/16 tickets were eligible and neither eligible team was wrong. At 20%, 10/16 were eligible, including one wrong team assignment. Five predicted actions required approval under all three policies; that count includes an incorrect cancellation prediction.

These are visible synthetic examples, not a held-out benchmark or evidence of general superiority. Read [the full results](evidence/presentation-v2/evaluation.json) and [the presentation walkthrough](PRESENTATION.md) to explain both the capabilities and the errors.

## Evaluate the trade-offs

**Evaluate samples** runs 16 visible synthetic examples: routine requests, outages, refunds, cancellation, negation, typos, paraphrases, ambiguous text and multiple requests. Labels are demonstration expectations, not adjudicated production ground truth; ambiguous cases can reasonably need discussion.

The report shows department agreement against a keyword baseline, requested-action agreement, latency, automatic-routing eligibility and wrong auto-routes. The comparison table reuses the same predictions across all three policies. Its error denominator is the number of eligible routes; zero eligible routes is shown as N/A, not perfect accuracy. Action approval is reported separately.

These are not held-out examples and the thresholds have not been calibrated. Less review alone is not evidence of improvement. No LLM comparison, financial saving or production-accuracy claim is established. The keyword baseline is intentionally simple and covers only department classification.

## Tests and evidence

```bash
"$HOME/Library/Application Support/LayaDecisionLab/venv/bin/python" -m unittest discover -s tests -v
```

The tests cover routing/approval separation, urgency and retention, uncertain actions, threshold boundaries, policy comparisons, HTTP validation and policy recalculation without inference.

With the native server running, install the optional browser-test dependencies (Node.js 20+) and execute:

```bash
npm ci
npx playwright install chromium
npm run test:browser
```

The browser test performs real inference and stores synthetic-ticket results and screenshots in `evidence/presentation-v2/`. It verifies policy edits preserve predictions and do not submit another inference, all 16 examples, metric counts, exports, guide links, Portuguese, and desktop/mobile layouts. `BASE_URL`, `EVIDENCE_DIR` and `EXPECT_DEVICE` can override the target, evidence directory and expected device.

Previous three-question/eight-sample results are preserved under `evidence/` and `evidence/docker/` as historical evidence. They do not measure the current four-question demo. Current measurements and presentation examples are described in [PRESENTATION.md](PRESENTATION.md).

## Implementation and limits

- FastAPI backend; HTML/CSS/JavaScript frontend, without CDNs. Local server only.
- Laya 0.4.15 and `convaiinnovations/laya` revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`; no paid inference APIs.
- Inputs are limited to 2,000 characters and 450 checkpoint tokens. Inference is serialized; concurrent model requests receive HTTP 409. Failures are shown rather than replaced by simulated predictions.
- Inference time includes the SDK call and MPS synchronization, but excludes model downloads, loading and HTTP overhead. Server total time is separate. Sample p95 uses nearest rank and can include first inferences after loading.
- Custom ticket text is not stored by the application or sent to a remote inference API. JSON files are saved only when explicitly exported; committed evidence contains synthetic samples.
- The SDK warns about checkpoint temperatures for some entries. Confidence remains uncalibrated; structured output can still be semantically wrong.
- Adding the requested-action question did not train or fine-tune the model. A schema is an input contract, not learned domain expertise.

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

After running all 16 samples to cache both checkpoints, recreate the service in offline mode:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 docker compose up -d --no-build --force-recreate
```

If using the alternate port, prepend `LAYA_PORT=8766` to that command. To return to online mode, recreate with both offline variables set to `0`. Offline mode requires the image and both checkpoints to have been downloaded first.

To repeat the browser checks against Docker without replacing the native-run evidence:

```bash
npm ci
npx playwright install chromium
BASE_URL=http://127.0.0.1:8765 EXPECT_DEVICE=cpu EVIDENCE_DIR=evidence/docker-v2 npm run test:browser
```

Use port 8766 in `BASE_URL` if that is where the container is running. These checks execute real local inference, including all 16 samples.

The current four-question version also passed eight Python tests and real English/Portuguese inference in a network-isolated Docker CPU container on October 26, 2026. See `evidence/docker-v2/offline-result.json`. The current full browser flow was tested natively on Metal.

### Docker validation history

The original Docker installation was validated on October 25, 2026 on Apple Silicon (`linux/arm64`), Docker Desktop 4.42.1, Engine 28.2.2 and Compose 2.37.1, with 8 CPUs and approximately 7.65 GiB allocated. PyTorch `2.14.1+cpu` avoids CUDA downloads. Windows and `linux/amd64` have not been validated.

That run covered a fresh model volume, real browser inference, both checkpoints in a new `--network none` container, and healthy offline recreation. Original evidence is in `evidence/docker/validation.json`; its eight-sample metrics belong to the previous schema.

After caching both models, repeat the current network-isolated inference check:

```bash
docker run --rm -i --network none -v laya-decision-lab_models:/models laya-decision-lab:local python - < tests/docker_offline.py
```

## Sources

- [Official Laya source and limitations](https://github.com/NandhaKishorM/laya)
- [Typed questions and answers](https://github.com/NandhaKishorM/laya/blob/main/docs/questions-and-answers.md)
- [Python distribution](https://pypi.org/project/laya/)
- [Public model weights](https://huggingface.co/convaiinnovations/laya)
- [PyTorch CPU installation](https://pytorch.org/get-started/locally/)
