FROM python:3.11

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt
RUN pip install flask-sqlalchemy

CMD ["python", "app.py"]
