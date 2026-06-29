"""
Django Base Settings - Configuración compartida para todos los entornos
Configurado para Railway con CORS abierto
"""

import pymysql
pymysql.install_as_MySQLdb()

from pathlib import Path
from decouple import config
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ============================================
# 🔐 SECURITY CONFIGURATION
# ============================================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-smarterp-clave-secreta-2024-abc123xyz')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

# ============================================
# 🔓 CORS CONFIGURATION - ACEPTAR TODO
# ============================================
CORS_ALLOW_ALL_ORIGINS = True  # ← Permite peticiones desde cualquier origen
CORS_ALLOW_CREDENTIALS = True  # ← Permite cookies y headers de autenticación

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-business-id',  # Header personalizado
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# ============================================
# 🔒 CSRF CONFIGURATION
# ============================================
CSRF_TRUSTED_ORIGINS = [
    'https://smarterp-auth-api-production.up.railway.app',
    'https://smarterp-frontend-production.up.railway.app',
    'https://*.up.railway.app',
    'https://*.railway.app',
]

# Si DEBUG está activo, agregar orígenes locales
if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend([
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5173',
        'http://127.0.0.1:5173',
    ])

# Configuraciones de seguridad
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ============================================
# 📦 APPLICATION DEFINITION
# ============================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.business_roles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
]

LOCAL_APPS = [
    'apps.authentication.apps.AuthenticationConfig',
    'apps.business.apps.BusinessConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================
# 🔧 MIDDLEWARE CONFIGURATION
# ============================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # ← DEBE IR ANTES DE CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.authentication.middleware.BusinessContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ============================================
# 👤 AUTHENTICATION
# ============================================
AUTH_USER_MODEL = 'authentication.CustomUser'

# ============================================
# 🗄️ DATABASE CONFIGURATION
# ============================================
def get_database_config():
    # Intentar 1: MYSQL_URL (formato preferido de Railway)
    mysql_url = os.environ.get('MYSQL_URL') or os.environ.get('MYSQL_PUBLIC_URL')
    if mysql_url:
        print(f"✅ Usando MYSQL_URL para conexión")
        import dj_database_url
        return {
            'default': dj_database_url.parse(mysql_url, conn_max_age=600)
        }
    
    # Intentar 2: Variables individuales de Railway
    db_name = os.environ.get('MYSQLDATABASE') or os.environ.get('MYSQL_DATABASE') or config('DB_NAME', default='railway')
    db_user = os.environ.get('MYSQLUSER') or os.environ.get('MYSQL_USER') or config('DB_USER', default='root')
    db_password = os.environ.get('MYSQLPASSWORD') or os.environ.get('MYSQL_PASSWORD') or os.environ.get('MYSQL_ROOT_PASSWORD') or config('DB_PASSWORD', default='')
    db_host = os.environ.get('MYSQLHOST') or os.environ.get('MYSQL_HOST') or config('DB_HOST', default='localhost')
    db_port = os.environ.get('MYSQLPORT') or os.environ.get('MYSQL_PORT') or config('DB_PORT', default='3306')
    
    print(f"✅ Usando variables individuales - DB: {db_name}, Host: {db_host}")
    
    return {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': db_password,
            'HOST': db_host,
            'PORT': db_port,
            'OPTIONS': {
                'charset': 'utf8mb4',
                'connect_timeout': 10,
            },
            'CONN_MAX_AGE': 600,
        }
    }

DATABASES = get_database_config()

# ============================================
# 🔐 PASSWORD VALIDATION
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================
# 🌍 INTERNATIONALIZATION
# ============================================
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# ============================================
# 📁 STATIC FILES
# ============================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# 🔑 REST FRAMEWORK & JWT
# ============================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'EXCEPTION_HANDLER': 'apps.authentication.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'TOKEN_OBTAIN_SERIALIZER': 'apps.authentication.serializers.CustomTokenObtainPairSerializer',
}

# ============================================
# 🔧 CORS FALLBACK - Middleware personalizado
# ============================================
class ForceCORSMiddleware:
    """
    Middleware que fuerza headers CORS en TODAS las respuestas.
    Esto soluciona problemas cuando django-cors-headers no funciona correctamente.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Forzar headers CORS en TODAS las respuestas
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Business-ID, X-Requested-With'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Max-Age'] = '86400'
        
        # Manejar preflight requests (OPTIONS)
        if request.method == 'OPTIONS':
            response.status_code = 200
            response.content = ''
            
        return response

# Agregar middleware al inicio de la lista
MIDDLEWARE.insert(0, 'config.settings.base.ForceCORSMiddleware')

# ============================================
# 🔧 DEBUG - Imprimir configuración CORS
# ============================================
print("=" * 80)
print("🔧 DJANGO SETTINGS CARGADOS")
print(f"✅ CORS_ALLOW_ALL_ORIGINS: {CORS_ALLOW_ALL_ORIGINS}")
print(f"✅ CORS_ALLOW_CREDENTIALS: {CORS_ALLOW_CREDENTIALS}")
print(f"✅ ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"✅ DEBUG: {DEBUG}")
print("=" * 80)