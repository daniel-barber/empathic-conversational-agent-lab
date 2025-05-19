# syntax=docker/dockerfile:1
FROM python:3.10-slim
WORKDIR /empathic-conversational-agent-lab
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run","frontend/app.py"]