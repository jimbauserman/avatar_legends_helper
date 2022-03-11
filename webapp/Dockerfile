# pull from python image
FROM python:3.7

# Set working directory for app
WORKDIR /webapp

# Install needed packages
COPY requirements.txt /webapp
RUN pip install -r requirements.txt

# Run app when container launches
COPY flask_api.py /webapp
COPY db_utils.py /webapp
COPY logging_conf.yaml /webapp
CMD python flask_api.py