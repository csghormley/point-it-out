# build a GDAL-enabled Django environment
# to build this Dockerfile, run the following command from the directory
# ABOVE the Django project
# docker build . -f<folder-containing-this-Dockerfile>

# pull base image containing dependencies
FROM csghor/mapsurvey-deps:latest

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# create a fresh virtual environment in 'venv',
# and install the required packages
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN . /opt/venv/bin/activate
COPY ./requirements.txt .

RUN pip install -r requirements.txt && \
    pip install --upgrade pip
