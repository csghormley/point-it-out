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

# install uv for faster dependency installation
RUN pip install --upgrade pip uv

# copy dependency files
COPY ./pyproject.toml .
COPY ./uv.lock .

# create a fresh virtual environment and install dependencies with uv
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv sync --frozen
