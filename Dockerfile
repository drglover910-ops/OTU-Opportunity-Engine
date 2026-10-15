FROM python:3.12-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN python -m playwright install --with-deps chromium && chmod -R a+rX /opt/playwright
COPY --chown=appuser:appuser app.py engine.py applications.py mail_history.py platform_browser.py contra_mcp.py document_review.py document_preview.py assistant_knowledge.json matrix.js ui.html ui.js ui.css playbooks.json VERSION /app/
USER appuser
ENV PORT=7860
EXPOSE 7860
CMD ["python", "app.py"]
