FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install LibreOffice with full filters
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:libreoffice/ppa -y \
    && apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    libreoffice-java-common \
    libreoffice-common \
    uno-libs-private \
    ure \
    python3 \
    python3-pip \
    fonts-dejavu-core \
    fonts-liberation \
    poppler-utils \
    default-jre \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
