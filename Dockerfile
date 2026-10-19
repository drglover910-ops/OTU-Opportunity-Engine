FROM python:3.12-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY scripts/fetch_voice_model.py /tmp/fetch_voice_model.py
RUN python /tmp/fetch_voice_model.py /opt/otu-voice && chmod -R a+rX /opt/otu-voice
ENV OTU_VOICE_MODEL_DIR=/opt/otu-voice
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN python -m playwright install --with-deps chromium && chmod -R a+rX /opt/playwright
COPY --chown=appuser:appuser cpu_voice.py voice_worker.py app.py engine.py knowledge_store.py contra_applications.py opportunity_review.py research_tools.py chat_service.py workspace_ops.py backup_store.py applications.py mail_history.py platform_browser.py contra_mcp.py document_review.py designed_resume.py attachment_store.py document_preview.py assistant_knowledge.json matrix.js ui.html ui.js ui.css playbooks.json VERSION /app/
COPY --chown=appuser:appuser voice_samples/ /app/voice_samples/
USER appuser
ENV PORT=7860
EXPOSE 7860
CMD ["python", "app.py"]
