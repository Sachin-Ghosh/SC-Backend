#!/usr/bin/env bash
# exit on error
set -o errexit

# Store the project root directory
PROJECT_ROOT=$(pwd)

# Create directories
echo "Creating directories..."
mkdir -p $HOME/tesseract
cd $HOME/tesseract

# Install build dependencies
echo "Installing build dependencies..."
pip install Cython
pip install numpy

# Install Leptonica first
echo "Installing Leptonica..."
rm -rf leptonica  # Remove if exists
git clone --depth 1 https://github.com/DanBloomberg/leptonica.git
cd leptonica
./autogen.sh
./configure --prefix=$HOME/local/
make
make install
export PKG_CONFIG_PATH=$HOME/local/lib/pkgconfig:$PKG_CONFIG_PATH
export LD_LIBRARY_PATH=$HOME/local/lib:$LD_LIBRARY_PATH
cd ..

# Clone Tesseract repository
echo "Cloning Tesseract repository..."
rm -rf tesseract  # Remove if exists
git clone --depth 1 https://github.com/tesseract-ocr/tesseract.git
cd tesseract

# Build and install Tesseract
echo "Building Tesseract..."
./autogen.sh
./configure --prefix=$HOME/local/ LIBLEPT_HEADERSDIR=$HOME/local/include/
make
make install

# Add Tesseract to PATH
export PATH="$HOME/local/bin:$PATH"

# Download English language data
echo "Downloading language data..."
cd $HOME/tesseract
rm -rf tessdata  # Remove if exists
git clone --depth 1 https://github.com/tesseract-ocr/tessdata.git
export TESSDATA_PREFIX="$HOME/tesseract/tessdata"

# Return to project directory
cd $PROJECT_ROOT

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

# Create requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    echo "Creating requirements.txt..."
    cat > requirements.txt << EOL
django>=4.2.0
djangorestframework>=3.14.0
django-cors-headers>=4.3.0
pillow>=10.0.0
pytesseract>=0.3.10
python-dotenv>=1.0.0
gunicorn>=21.2.0
psycopg2-binary>=2.9.9
whitenoise>=6.6.0
EOL
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install gunicorn
echo "Installing gunicorn..."
pip install gunicorn

# Create necessary directories
mkdir -p staticfiles media

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations
echo "Running migrations..."
python manage.py migrate --no-input

# Create superuser if none exists
echo "Creating superuser if none exists..."
python manage.py create_superuser_if_none_exists

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

# Update settings with Tesseract path
echo "
# Tesseract Configuration
TESSERACT_CMD = '$HOME/local/bin/tesseract'
TESSDATA_PREFIX = '$HOME/tesseract/tessdata'
" >> sc_backend/settings.py