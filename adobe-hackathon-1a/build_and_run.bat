@echo off
echo Building Docker image...
docker build --platform linux/amd64 -t pdf-structure-extractor:latest .

echo Running Docker container...
docker run --rm -v "%cd%\input":/app/input -v "%cd%\output":/app/output --network none pdf-structure-extractor:latest

echo Done!