FROM python:3.13-bookworm

RUN apt-get update && \
    apt-get install -y openjdk-17-jdk wget curl git && \
    apt-get clean

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:10000", "app:app"]
