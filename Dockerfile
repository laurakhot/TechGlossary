# Use full Python image to avoid slim image repo issues
FROM python:3.13

# Install Java JDK and necessary tools
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk wget curl git && \
    apt-get clean

# Set JAVA_HOME for PyTerrier
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Set working directory for the app
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . .

# Expose port
EXPOSE 10000

# Command to run the Flask app with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:10000", "app:app"]