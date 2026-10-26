FROM python:3.11-slim
WORKDIR /app
COPY requirements.lock.txt .
# Use the CPU wheel to avoid downloading CUDA libraries in Docker Desktop.
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.lock.txt \
    && pip check
COPY app.py domain.py questions.json samples.json ./
COPY static ./static
ENV HF_HOME=/models HF_HUB_DISABLE_IMPLICIT_TOKEN=1 LAYA_LAB_DEVICE=cpu
EXPOSE 8765
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8765"]
