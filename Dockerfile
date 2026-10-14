FROM python:3.12-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY --chown=appuser:appuser app.py /app/app.py
USER appuser
ENV PORT=7860
EXPOSE 7860
CMD ["python", "app.py"]
