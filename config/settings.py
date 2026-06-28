import pymysql
pymysql.install_as_MySQLdb()

import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-fallback-key')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

# 🔧 Database configuration para Railway
# Railway usa MYSQLHOST, MYSQLPASSWORD, etc. (sin underscore)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQLDATABASE', config('DB_NAME', default='smarterp_db')),
        'USER': os.environ.get('MYSQLUSER', config('DB_USER', default='root')),
        'PASSWORD': os.environ.get('MYSQLPASSWORD', config('DB_PASSWORD', default='')),
        'HOST': os.environ.get('MYSQLHOST', config('DB_HOST', default='localhost')),
        'PORT': os.environ.get('MYSQLPORT', config('DB_PORT', default='3306')),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
}