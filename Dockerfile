FROM python:3.8-alpine

WORKDIR /var/www
COPY requirements.txt .
RUN apk --update add libffi-dev openssl-dev py-pip build-base gcc nodejs-npm

RUN pip3 install --no-cache-dir -r requirements.txt

COPY client ./client
RUN cd client && npm install && npm run build

ENTRYPOINT ["python3", "main.py", "-debuglog"]