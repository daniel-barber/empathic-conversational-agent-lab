# syntax=docker/dockerfile:1
FROM python:3.10-slim
WORKDIR /empathic-conversational-agent-lab
ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["flask", "run", "--debug"]