FROM python

COPY . /app
WORKDIR /app

RUN pip install uwsgi pytest pytest-runner
RUN pip install -e .

EXPOSE 5000
CMD ["uwsgi", "--http", "0.0.0.0:5000", "--wsgi-file", "/app/wsgi.py", "--processes", "4", "--threads", "2"]
