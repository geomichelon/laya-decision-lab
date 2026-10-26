"""Verify both cached checkpoints in a fresh container without network access."""
import contextlib
import json
import os
import sys

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['LAYA_LAB_PRELOAD'] = '0'

with contextlib.redirect_stdout(sys.stderr):
    import torch
    from app import Engine, SAMPLES

    assert torch.version.cuda is None, 'Expected a CPU-only PyTorch build'
    engine = Engine()
    results = []
    for sample_id, model in [('duplicate', 'typed-decisions'), ('pt-billing', 'multilingual')]:
        sample = next(item for item in SAMPLES if item['id'] == sample_id)
        result = engine.predict(sample['text'], model, .8)
        assert result['mode'] == 'real_local_inference'
        assert result['device'] == 'cpu'
        assert result['answers']['department']['choice'] == 'billing'
        results.append({'sample': sample_id, 'result': result})

print(json.dumps({'passed': True, 'torch': torch.__version__, 'results': results}, indent=2))
