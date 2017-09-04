FROM python

COPY . /app
WORKDIR /app

RUN set -x; \
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main" > /etc/apt/sources.list.d/pgdg.list' \
    && curl -s https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uwsgi pytest pytest-runner mock awscli
RUN pip install -e .

EXPOSE 5000
CMD ["uwsgi", "--http", "0.0.0.0:5000", "--wsgi-file", "/app/wsgi.py", "--processes", "4", "--threads", "2"]
