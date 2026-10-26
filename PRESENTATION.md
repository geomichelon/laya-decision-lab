# Presenting Laya Decision Lab

## The message to remember

**Laya predicts bounded signals from text. The application applies an explicit policy. A prediction is neither a business rule nor permission to act.**

This demo is a teaching tool with real local inference. Its 16 visible synthetic tickets are not a production benchmark, and its policy thresholds are not calibrated recommendations.

## Six-minute walkthrough

### 0:00–0:45 — The problem

“Support teams receive free-form requests, but their workflow needs concrete fields: a responsible team, a priority and a next action. We want to inspect those decisions before connecting any automation.”

Show the four steps above **Live demo**: ticket, Laya signals, application policy and proposed workflow.

### 0:45–1:45 — One ticket, four typed outputs

Load **Routine invoice copy** and click **Analyze ticket**. Expand **Inspect the four Laya signals**.

“The same text goes into one SDK prediction call with four explicit questions. We receive a department label, an urgency score, a cancellation signal and a requested-action label. We are not asking the model to write a customer response.”

Distinguish probability from confidence. A category's probability and the SDK's confidence are different values. Neither guarantees that the answer is correct.

In the recorded run, the department and information request were correct, but the priority rule mapped an urgency score of about 0.58 to Medium despite the ticket saying there was no rush. Use that disagreement to explain why even a correct team assignment is not the same as a fully correct workflow.

### 1:45–2:30 — Policy changes without another model call

Switch from **Conservative** to **Exploratory**. Show the “same prediction / no new Laya inference” message.

“The model has not changed its mind. The prediction and inference ID remain unchanged. We have changed how much uncertainty our routing policy accepts.”

The routine invoice had department confidence of approximately 36% in the recorded run, so an 80% rule requests team review while a 20% rule makes it eligible for routing. These numbers are illustrative; a lower threshold is not automatically better.

### 2:30–3:15 — Routing is not approval

Load **Duplicate charge**, analyze it and choose **Exploratory**.

“The model identifies Billing and a refund request. Routing can be eligible while the refund still requires a person's approval. High urgency sets priority. It does not by itself make the team assignment uncertain.”

Expand **Why this policy outcome?**. This is a deterministic rule trace, not a generated explanation of the model's hidden reasoning. Nothing is routed, refunded or cancelled by the demo.

### 3:15–4:15 — Show both capability and failure

Try **Login with typos** or **No technical keywords**. In the recorded evaluation Laya identified Technical, while the simple keyword baseline returned Other. This illustrates a potential benefit beyond literal keyword matching on these particular examples.

Then show **Routine invoice in Portuguese**. It explicitly says the customer does not want cancellation or a refund, yet the recorded action prediction was cancellation. This is a useful failure: an accurate department does not guarantee an accurate action, and a structured answer can be wrong.

Do not change the sample or hide the error to make the demonstration appear more successful. Use a ticket supplied by the audience if time permits.

### 4:15–5:15 — Quantify the trade-off

Open **Evaluate samples** and run the 16 examples. The run is grouped by language to reduce checkpoint reloads. Models remain resident one at a time, so allow for loading when languages change.

Discuss three separate measures:

- Department agreement: whether the predicted team matches the demonstration label.
- Routing coverage and wrong auto-routes: how many predictions the policy would accept, and how many of those are wrong.
- Action agreement and approval: the action prediction can be wrong independently, while approvals remain a separate policy decision.

In the recorded run, Laya agreed with 15/16 department labels and the keyword rules with 14/16. Requested-action agreement was 12/16. This small, visible set does not establish general superiority or production accuracy.

### 5:15–6:00 — Close with the adoption question

“The useful capability is a locally runnable model returning typed signals that application code can inspect. Its business value depends on accuracy and error costs in our workflow. Before automating real work, we need representative tickets, agreed labels, calibrated thresholds and an independent evaluation.”

## What benefits can we demonstrate?

| Potential benefit | What to show | What not to claim |
|---|---|---|
| Application-ready outputs | Four fields and JSON export | Structured means correct |
| More flexible matching than literal keywords | Typo/paraphrase examples versus the baseline | Better than every rules system or every LLM |
| Local execution | MPS/CPU indicator; cached offline tests | Zero compute cost or no hardware requirements |
| Several questions in one call | Fixed decision schema and four returned signals | A latency or cost advantage over an untested alternative |
| Explicit, changeable policy | Change threshold without another inference | The policy fixes model errors |
| Inspectable decisions | Rule trace, model revision, inference ID and evaluation exports | The trace exposes the model's internal reasoning |

The upstream project documents typed choice, score and yes/no decisions. This demo verifies one SDK prediction call returning four signals; it does not benchmark architectural claims against other model families. Sources: [Laya](https://github.com/NandhaKishorM/laya), [question and answer types](https://github.com/NandhaKishorM/laya/blob/main/docs/questions-and-answers.md).

## Questions you may be asked

**Why is the threshold not an accuracy percentage?** Confidence is a model output. Accuracy is measured against labeled examples. We have not calibrated confidence for these tickets, and the SDK reports a checkpoint-temperature warning.

**Why do Conservative and Balanced sometimes produce the same coverage?** Only predictions whose confidence lies between 50% and 80% can change routing between those presets. If there are none in this sample, their coverage is identical.

**Can a low threshold authorize a refund?** No. A predicted refund or cancellation always requires approval. However, a model can miss the action entirely; this rule alone is not sufficient protection for real financial automation.

**Can we replace a generative LLM?** Evaluate Laya for bounded decisions with explicit output types. This application does not generate customer replies, long explanations or plans, and it has no measured LLM comparison.

**Does a correction train the model?** No. This version does not train or fine-tune Laya. Samples are evaluation inputs; their expected labels are never included in the inference request.

**What is the next production step?** Assemble a representative dataset, agree on ambiguous labels, separate development/calibration/test data, measure mistakes by consequence and compare credible baselines. Start with proposed routing and human review before integrating actions.

## Presentation checklist

- Start the native app with `bash start.command` and open http://127.0.0.1:8765.
- Run an English and a Portuguese sample before presenting to cache both checkpoints; switching them still takes loading time.
- Use **Present** for fullscreen. Keep the local server terminal open.
- Keep the policy at 80% at the beginning, then deliberately change it to 20% to explain the trade-off.
- Show at least one model error and clarify that all tickets are synthetic.
- Use the presentation slides as the introduction. This application adds real inference and a separate operational policy; it does not establish the production claims a pilot would need to test.

## Recorded policy comparison — October 26, 2026

| Preset | Routing candidates | Team reviews | Wrong eligible routes | Predicted actions needing approval |
|---|---:|---:|---:|---:|
| Conservative, 80% | 2/16 | 14/16 | 0/2 | 5/16 |
| Balanced, 50% | 2/16 | 14/16 | 0/2 | 5/16 |
| Exploratory, 20% | 10/16 | 6/16 | 1/10 | 5/16 |

Approval counts reflect predicted actions; they are not proof that those predictions are correct. The Portuguese invoice example incorrectly contributed an approval request. Across all 16 examples, department agreement was 15/16, keyword-baseline agreement 14/16 and requested-action agreement 12/16. Native Metal inference p50 was 222.78 ms and p95 was 236.27 ms in the final grouped run, excluding downloads, model loading and HTTP. A previous ungrouped run measured p95 323.33 ms; workload and warmup affect timing. Do not present these as production service-level guarantees.

Eight Python tests and the real Chromium desktop/mobile flow passed. Four-signal inference also passed for both checkpoints in a Docker CPU container with network disabled. No truncation or CPU fallback was observed across the native evaluation. The native app remains the presentation runtime; Docker is an alternative.

See [the validation report](evidence/presentation-v2/validation.json), [all predictions and labels](evidence/presentation-v2/evaluation.json), and [Docker offline results](evidence/docker-v2/offline-result.json).
