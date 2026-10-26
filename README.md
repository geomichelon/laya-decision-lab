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
