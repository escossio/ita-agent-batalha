FROM python:3.13-slim@sha256:7c61056e61ac89e852de05f3dc6fa51a6dd2181797bceed46aa725dd7cb2cd3b
ARG COMPONENT
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-agent.txt requirements-data.txt requirements-gcp.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN if [ "$COMPONENT" = agent ]; then pip install --no-cache-dir -r /app/requirements-agent.txt; fi
RUN if [ "$COMPONENT" = data ]; then pip install --no-cache-dir -r /app/requirements-data.txt; fi
COPY packages/runtime/ /app/packages/runtime/
COPY packages/contracts/ /app/packages/contracts/
COPY config/rules.json /app/config/rules.json
COPY services/${COMPONENT}/ /app/component/
USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "component.main"]
