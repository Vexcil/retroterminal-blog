FROM python:3.12-slim
RUN pip install --no-cache-dir 'requests>=2.32.5,<3'
WORKDIR /app
COPY build_tab_index.py /app/
COPY --chown=1000:1000 scripts /app/scripts
USER 1000:1000
EXPOSE 4080
CMD ["python3", "scripts/tabs_host_server.py", "--host", "0.0.0.0", "--port", "4080", "--data-dir", "/data", "--files-dir", "/tabs", "--play-counts-file", "/data/play-counts.json"]
