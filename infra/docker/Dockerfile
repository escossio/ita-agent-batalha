FROM python:3.13-slim@sha256:7c61056e61ac89e852de05f3dc6fa51a6dd2181797bceed46aa725dd7cb2cd3b
ARG COMPONENT
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY packages/runtime/ /app/packages/runtime/
COPY services/${COMPONENT}/ /app/component/
USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "component.main"]
