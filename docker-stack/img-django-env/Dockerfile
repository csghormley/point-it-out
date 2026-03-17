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

# copy uv binary from official image,
# for faster dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# copy dependency files
COPY ./pyproject.toml .
COPY ./uv.lock .
COPY ./README.md .

# create a fresh virtual environment and install dependencies with uv
# Use UV_PROJECT_ENVIRONMENT to force uv to install into /opt/venv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv sync --frozen
