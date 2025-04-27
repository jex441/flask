# Quickstart

## Start the Client:

`cd helix`

`pnpm install`

`pnpm run dev`

## In a separate terminal

`source venv activate` (Mac)

### Create database tables:

`python3`

`from api import app, db
with app.app_context:
    db.create_all()`

`exit()`

### Install requirements

`pip3 install -r requirements.txt`

### Run app:

`flask --app api run --port=8000`

# Visit in your browser

`http://localhost:5173/`
