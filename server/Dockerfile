FROM python

COPY docker-entrypoint.sh /
COPY . /app
WORKDIR /app

RUN set -x; \
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main" > /etc/apt/sources.list.d/pgdg.list' \
    && curl -s https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uwsgi pytest pytest-runner mock
RUN pip install -e .

ENTRYPOINT ["/docker-entrypoint.sh"]

ENV UWSGI_PROCESSES=4, \
    FLASK_APP=dumpbagserver

EXPOSE 5000
CMD uwsgi --socket :5000 --wsgi-file /app/wsgi.py --processes $UWSGI_PROCESSES
