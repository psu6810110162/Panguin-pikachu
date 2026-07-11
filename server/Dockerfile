# Backend only — the Kivy game (game/, screens/, ui/, assets/) is a desktop GUI app
# and gets nothing from being containerized (no display, no audio, no input device).
# See docs/adr/008-docker-compose-backend.md.

FROM python:3.12-slim

WORKDIR /app

COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# COPY . . (not selective per-package COPY) so a future shared package under core/ or
# elsewhere doesn't silently go missing from the image — .dockerignore is the one place
# that decides what's excluded, not a list of COPY lines that can go stale.
COPY . .

# Run as a non-root user — standard defense-in-depth: a compromised Flask process
# shouldn't own the container's filesystem. Created after COPY so the layer cache for
# deps/source stays intact.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5000/healthz', timeout=2).status == 200 else 1)"

CMD ["python", "-m", "server"]
