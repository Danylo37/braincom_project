# Braincom Project

## Project Setup

### 1. Install Dependencies

Before starting the project, install all required dependencies:

```bash
pip install -r requirements.txt
```

After installing Python dependencies, you need to install the Chromium browser for Playwright:

```bash
playwright install chromium
```

### 2. Environment Configuration

All project settings are stored in the `.env` file. This file is used by both Django (settings.py) and Docker Compose.

Copy the `.env.example` file to `.env` and edit it:

```bash
cp .env.example .env
```

### 3. Environment Variables

#### Django Settings:
- `SECRET_KEY` - Django secret key (must be changed in production)
- `DEBUG` - debug mode (True/False)
- `ALLOWED_HOSTS` - allowed hosts (comma-separated)

#### Database Settings:
- `DB_NAME` - database name
- `DB_USER` - PostgreSQL user
- `DB_PASSWORD` - PostgreSQL user password
- `DB_HOST` - database host (localhost for local development)
- `DB_PORT` - PostgreSQL port (default 5432)

### 4. Running the Project

#### Start the database via Docker:
```bash
# Run in foreground (see logs in terminal)
docker-compose up

# Run in background (detached mode)
docker-compose up -d
```

#### Stop Docker containers:
```bash
# Stop and remove containers
docker-compose down

# Stop containers but keep them
docker-compose stop

# View running containers
docker-compose ps
```

#### Start the Django server:
```bash
cd braincom_project
python manage.py migrate
python manage.py runserver
```

## Configuration Structure

All configuration data is centralized in the `.env` file:
- **docker-compose.yml** - uses variables from `.env` to configure the PostgreSQL container
- **settings.py** - uses variables from `.env` via python-dotenv to configure Django

This ensures a single source of configuration for the entire project.

## Database Management

### Clear the Database

To completely clear the database and reset the schema:

```bash
docker exec -it braincom_postgres psql -U braincom_user -d braincom_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO braincom_user; GRANT ALL ON SCHEMA public TO public;"
```

After clearing the database, don't forget to run migrations again:

```bash
cd braincom_project
python manage.py migrate
```

## Data Export

### Export Products to CSV

To export all products from the database to a CSV file:

```bash
docker exec -i braincom_postgres psql -U braincom_user -d braincom_db -c "\COPY parser_app_product TO '/tmp/products.csv' CSV HEADER"
mkdir ./results
docker cp braincom_postgres:/tmp/products.csv ./results/products.csv
docker exec braincom_postgres rm /tmp/products.csv
```

This will create a `products.csv` file in the `results/` directory with all product data.

