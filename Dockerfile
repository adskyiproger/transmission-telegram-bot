FROM python:3.14.6-slim-bookworm

ARG PIPENV_RELEASE=2026.0.3

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /usr/src/app

COPY Pipfile Pipfile.lock ./
RUN python -m pip install --no-cache-dir "pipenv==${PIPENV_RELEASE}" && \
    pipenv sync --system && \
    python -m pip uninstall --yes pipenv virtualenv

RUN groupadd --gid 2022 python && \
    useradd --gid 2022 --uid 2022 --create-home \
      --home-dir /usr/src/app python

COPY --chown=python:python lib lib
COPY --chown=python:python models models
COPY --chown=python:python templates templates
COPY --chown=python:python torrentino.py .

RUN mkdir -p config logs && chown -R python:python config logs

USER python

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD ["python", "-c", "assert b'torrentino.py' in open('/proc/1/cmdline', 'rb').read()"]

ENTRYPOINT ["python", "./torrentino.py"]
