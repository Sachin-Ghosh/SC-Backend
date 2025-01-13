from .settings import *

DEBUG = True

# Add S3 settings
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'aurora2k24'
AWS_S3_REGION_NAME = 'ap-south-1'  # e.g., 'us-east-1'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERIFY = True
AWS_QUERYSTRING_AUTH = False

DATABASES = {
        'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'Backend',
        'USER': 'superuser',
        'PASSWORD': os.environ.get('DJANGO_SUPERUSER_PASS'),
        'HOST': 'backend.cx04ay8uggno.ap-south-1.rds.amazonaws.com',
        'PORT': '5432',
    }
}   

AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
STATIC_LOCATION = 'static'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/'

    # S3 media settings
MEDIA_LOCATION = 'media'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIA_LOCATION}/'