#!/usr/bin/env bash
# exit on error
set -o errexit

# Add Tesseract repository
echo "Adding Tesseract repository..."
add-apt-repository -y ppa:alex-p/tesseract-ocr

# Update package lists
echo "Updating package lists..."
apt-get update

# Install Tesseract
echo "Installing Tesseract..."
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Print tesseract version if available
if command -v tesseract &> /dev/null; then
    echo "Tesseract is installed:"
    tesseract --version
    which tesseract
else
    echo "Warning: Tesseract is not installed"
fi

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install gunicorn
echo "Installing gunicorn..."
pip install gunicorn

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations
echo "Running migrations..."
python manage.py migrate --no-input

# Create superuser if none exists
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

# Print installed packages
echo "Installed packages:"
pip list