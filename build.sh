#!/usr/bin/env bash
# exit on error
set -o errexit

# Create a temporary directory for downloads
mkdir -p /tmp/tesseract
cd /tmp/tesseract

# Download and install Tesseract binary
echo "Downloading and installing Tesseract..."
wget https://github.com/tesseract-ocr/tesseract/releases/download/5.3.3/tesseract-5.3.3.tar.gz
tar xvf tesseract-5.3.3.tar.gz
cd tesseract-5.3.3
./configure
make
make install
ldconfig

# Return to original directory
cd -

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