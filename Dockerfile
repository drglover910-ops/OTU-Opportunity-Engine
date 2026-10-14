FROM python:3.12-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser app.py engine.py applications.py ui.html ui.js ui.css playbooks.json VERSION /app/
USER appuser
ENV PORT=7860
EXPOSE 7860
CMD ["python", "app.py"]
