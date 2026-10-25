FROM python:3.11-slim
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY app.py domain.py questions.json samples.json ./
COPY static ./static
ENV HF_HOME=/models HF_HUB_DISABLE_IMPLICIT_TOKEN=1 LAYA_LAB_DEVICE=cpu
EXPOSE 8765
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8765"]
