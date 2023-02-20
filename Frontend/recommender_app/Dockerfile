FROM python:3.10.8

WORKDIR /app

COPY requirements.txt requirements.txt
COPY recommender.py recommender.py
COPY indeed_tfidf.pkl indeed_tfidf.pkl
COPY indeed_data.pkl indeed_data.pkl
COPY jobsdb_data.pkl jobsdb_data.pkl
COPY words200_v2.model words200_v2.model


RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV FLASK_APP recommender

EXPOSE 8080

# ENTRYPOINT [ "python", "-u", "-m", "flask", "--app", "recommender", "run", "--host=0.0.0.0"]
# ENTRYPOINT ["python", "recommender.py"]
ENTRYPOINT ["waitress-serve", "--port=8080", "--call", "recommender:create_app"]