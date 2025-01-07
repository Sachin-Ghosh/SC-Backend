#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing system dependencies..."
apt-get update && apt-get install -y python3-pip python3-dev tesseract-ocr

# Verify Tesseract installation
echo "Verifying Tesseract installation..."
tesseract --version
which tesseract


echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing gunicorn..."
pip install gunicorn

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate --no-input

echo "Creating superuser if none exists..."
python manage.py create_superuser_if_none_exists

# Create necessary directories
mkdir -p staticfiles media

# Print environment information
echo "Environment Information:"
echo "PORT: $PORT"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "Current Directory: $(pwd)"
echo "Python Version: $(python --version)"
echo "Pip Version: $(pip --version)"
echo "Tesseract Version: $(tesseract --version)"
echo "Tesseract Path: $(which tesseract)"

# Print installed packages
echo "Installed packages:"
pip list