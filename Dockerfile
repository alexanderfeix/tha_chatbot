FROM python:3.10-slim

WORKDIR /app

USER root

COPY chatbot_requirements.txt .

RUN pip install -r chatbot_requirements.txt

COPY /app /app/app
COPY /backend/rag /app/backend/rag
COPY /backend/__init__.py /app/backend/__init__.py
COPY /data /app/data
COPY /scripts /app/scripts
COPY /static /app/static
COPY /streamlit_app.py /app/streamlit_app.py

CMD ["streamlit", "run", "streamlit_app.py"]
