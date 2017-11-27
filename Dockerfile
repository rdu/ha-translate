FROM debian:stretch

RUN apt-get update
RUN apt-get install -y python3 python3-pip wget htop vim mc
RUN pip3 install --upgrade pip
RUN apt-get install -y python3-all-dev python3-pip build-essential swig git libpulse-dev 
ENV LANG C.UTF-8
RUN pip3 install paho-mqtt
RUN pip3 install apiai
WORKDIR /home
COPY CommandProcessor.py /home/CommandProcessor.py
COPY Run.py /home/Run.py

ENTRYPOINT python3 /home/Run.py 
