git pull || { echo "Error: git pull failed"; exit 1; }
docker compose down
docker compose up --build -d
