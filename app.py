"""Laya Decision Lab: loopback-only presentation companion; no external action execution."""
import gc
import json
import logging
import os
from pathlib import Path
import threading
import time
import uuid
from typing import Literal
from contextlib import asynccontextmanager

ROOT = Path(__file__).resolve().parent
os.environ.setdefault('HF_HOME', str(ROOT / '.cache' / 'huggingface'))
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, field_validator
from domain import baseline, policy, compare_policies, POLICY_PRESETS

QUESTIONS = json.loads((ROOT / 'questions.json').read_text())
SAMPLES = json.loads((ROOT / 'samples.json').read_text())
MODEL_REPO = 'convaiinnovations/laya'
MODEL_REVISION = '55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851'
MODEL_NAMES = {'typed-decisions': 'English / typed decisions', 'multilingual': 'Multilingual / português'}
logger = logging.getLogger('laya-lab')

class Engine:
    def __init__(self):
        self.lock = threading.Lock()
        self.agent = None
        self.model = None
        self.state = 'idle'
        self.error = None
        self.device = None
        self.load_ms = None

    def load(self, model):
        if self.agent is not None and self.model == model:
            return False
        self.state, self.error = 'loading', None
        self.agent = None
        self.model = model
        gc.collect()
        import torch
        import laya
        torch.set_num_threads(4)
        self.device = os.getenv('LAYA_LAB_DEVICE') or ('mps' if torch.backends.mps.is_available() else 'cpu')
        if self.device == 'mps':
            torch.mps.empty_cache()
        start = time.perf_counter()
        self.agent = laya.load(MODEL_REPO, subfolder=model, revision=MODEL_REVISION, device=self.device, token=False)
        self.load_ms = round((time.perf_counter()-start)*1000, 1)
        self.state = 'ready'
        return True

    def predict(self, text, model, threshold):
        if not self.lock.acquire(blocking=False):
            raise HTTPException(409, 'The local model is busy. Wait for the current analysis to finish.')
        start = time.perf_counter()
        try:
            loaded = self.load(model)
            # Fixed schema plus a bounded state: reject long input instead of silently truncating it.
            if len(self.agent.tok.encode(text, add_special_tokens=False)) > 450:
                raise HTTPException(422, 'This demo accepts tickets up to 450 tokens. Shorten the text.')
            self.state = 'analyzing'
            import torch
            def sync():
                if str(self.agent.device).startswith('mps'):
                    torch.mps.synchronize()
            sync()
            inference_start = time.perf_counter()
            result = self.agent.predict(text, QUESTIONS, max_len=1024, head_max_len=256)
            sync()
            inference_ms = round((time.perf_counter()-inference_start)*1000, 2)
            self.state = 'ready'
            return {'inference_id': uuid.uuid4().hex, 'schema_version': 2,
                    'answers': result['answers'], 'policy': policy(result['answers'], threshold),
                    'policy_comparison': compare_policies(result['answers']),
                    'baseline': baseline(text), 'inference_ms': inference_ms,
                    'total_ms': round((time.perf_counter()-start)*1000, 2), 'loaded_this_request': loaded,
                    'model': model, 'model_revision': MODEL_REVISION, 'device': str(self.agent.device),
                    'cpu_fallback_count': self.agent.cpu_fallback_count,
                    'usage': result.get('usage', {}), 'mode': 'real_local_inference',
                    'calibration': 'Not calibrated on these demonstration tickets.'}
        except HTTPException:
            self.state = 'ready' if self.agent else 'idle'
            raise
        except Exception:
            logger.exception('Laya inference failed')
            self.state, self.error = 'error', 'Could not load or run Laya. Check the local terminal and try again.'
            raise HTTPException(503, self.error)
        finally:
            self.lock.release()

    def prepare(self):
        with self.lock:
            try:
                self.load('typed-decisions')
            except Exception:
                logger.exception('Laya preparation failed')
                self.state, self.error = 'error', 'Model preparation failed. Analyze a ticket to retry; see the local terminal for details.'

engine = Engine()

@asynccontextmanager
async def lifespan(app):
    if os.getenv('LAYA_LAB_PRELOAD', '1') == '1':
        threading.Thread(target=engine.prepare, daemon=True).start()
    yield

app = FastAPI(title='Laya Decision Lab', lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', 'testserver'])

@app.middleware('http')
async def local_origin(request: Request, call_next):
    origin = request.headers.get('origin')
    if request.method == 'POST' and origin and origin != str(request.base_url).rstrip('/'):
        return JSONResponse({'detail': 'Only requests from this local application are allowed.'}, status_code=403)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

class Analysis(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    model: Literal['typed-decisions', 'multilingual'] = 'typed-decisions'
    threshold: float = Field(default=.8, ge=0, le=1, allow_inf_nan=False)

    @field_validator('text')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Enter a ticket to analyze.')
        return value.strip()

class Confidence(BaseModel):
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)

class DepartmentAnswer(Confidence):
    choice: Literal['billing', 'technical', 'sales', 'other']

class UrgencyAnswer(Confidence):
    score: float = Field(ge=0, le=2, allow_inf_nan=False)

class CancellationAnswer(Confidence):
    noul: float = Field(ge=0, le=1, allow_inf_nan=False)

class ActionAnswer(Confidence):
    choice: Literal['information', 'refund', 'cancellation', 'technical_help', 'sales_inquiry', 'unclear']

class DecisionAnswers(BaseModel):
    department: DepartmentAnswer
    urgency: UrgencyAnswer
    churn_risk: CancellationAnswer
    requested_action: ActionAnswer

class PolicyRequest(BaseModel):
    answers: DecisionAnswers
    threshold: float = Field(ge=0, le=1, allow_inf_nan=False)

@app.post('/api/policy')
def recalculate_policy(body: PolicyRequest):
    return {'policy': policy(body.answers.model_dump(), body.threshold), 'inference_performed': False}

@app.get('/api/status')
def status():
    import laya
    return {'state': engine.state, 'error': engine.error, 'model': engine.model,
            'device': engine.device, 'load_ms': engine.load_ms, 'version': laya.__version__}

@app.get('/api/config')
def config():
    return {'samples': SAMPLES, 'questions': QUESTIONS, 'models': MODEL_NAMES, 'revision': MODEL_REVISION, 'policy_presets': POLICY_PRESETS, 'schema_version': 2}

@app.post('/api/analyze')
def analyze(body: Analysis):
    return engine.predict(body.text, body.model, body.threshold)

@app.get('/')
def index():
    return FileResponse(ROOT / 'static' / 'index.html')

app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
