# pull from python image
FROM python:3.7

# Set working directory for app
WORKDIR /webapp

# Install needed packages
COPY requirements.txt /webapp
RUN pip install -r requirements.txt

# Run app when container launches
COPY app_runner.py /webapp
COPY application /webapp/application
COPY templates /webapp/application/templates
COPY static /webapp/application/static/
CMD python app_runner.py