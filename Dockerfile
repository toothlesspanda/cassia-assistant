FROM python:3.7

# # Create app directory
WORKDIR /pysensors

# # Install app dependencies
COPY ./requirements.txt ./

RUN PYTHONPATH=/usr/bin/python3.7 pip install -r requirements.txt

# # Bundle app source
COPY /pysensors /pysensors

CMD [ "./server.py" ]