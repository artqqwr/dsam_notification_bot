FROM python:3.13-alpine

ENV APP_HOME=/app/

RUN mkdir -p ${APP_HOME}

WORKDIR ${APP_HOME}

COPY requirements.freeze ./

RUN python -m pip install --no-cache-dir -r requirements.freeze

COPY . .

CMD ["python", "main.py"]