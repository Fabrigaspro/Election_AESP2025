from pathlib import Path
import os
from environ import Env

env = Env()
Env.read_env()
ENVIRONMENT = env("ENVIRONMENT", default="production")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY') 

# SECURITY WARNING: don't run with debug turned on in production!
if ENVIRONMENT == "development":
    DEBUG = True  
else:
    DEBUG = False  

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'electionaesp2025iuget.up.railway.app', '.railway.app', ]

# ⚠️ Pour Railway - Configuration de sécurité
CSRF_TRUSTED_ORIGINS = [
    'https://electionaesp2025iuget.up.railway.app',
    'https://*.railway.app',
]

# Configuration CSRF critique
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # Doit être False pour que JavaScript puisse lire le token
CSRF_USE_SESSIONS = False
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

CSRF_COOKIE_DOMAIN = '.railway.app'  # Pour tous les sous-domaines Railway
CSRF_COOKIE_SAMESITE = 'Lax'  # 'None' peut causer des problèmes

# Configuration session
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'  # None Important pour les iframes et cross-origin
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 1209600

# Configuration sécurité
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage', 
    'cloudinary',
    'vote_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'election_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.csrf',
            ],
        },
    },
]

WSGI_APPLICATION = 'election_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
} 

POSTGRES_LOCALLY = False
if ENVIRONMENT == 'production' or POSTGRES_LOCALLY == True:
    import dj_database_url
    DATABASES['default']=dj_database_url.parse(env('DATABASE_URL'))

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True
USE_I18N = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

#
# Configuration Cloudinary
if ENVIRONMENT == 'production':
    # Utilise CLOUDINARY_URL si disponible
    CLOUDINARY_URL = env('CLOUDINARY_URL', default=None)
    
    if CLOUDINARY_URL:
        # Cloudinary peut lire directement CLOUDINARY_URL
        DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
        
        # Configuration pour la librairie cloudinary
        import cloudinary
        cloudinary.config(
            cloud_name=env('CLOUDINARY_CLOUD_NAME', default=''),  
            api_key=env('CLOUDINARY_API_KEY', default=''),
            api_secret=env('CLOUDINARY_API_SECRET', default=''),
            secure=True
        )
        
        print("✅ Configuration Cloudinary avec CLOUDINARY_URL")
    else:
        # Fallback vers l'ancienne configuration
        DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': env('CLOUDINARY_CLOUD_NAME', default=''),
            'API_KEY': env('CLOUDINARY_API_KEY', default=''),
            'API_SECRET': env('CLOUDINARY_API_SECRET', default=''),
        }
    MEDIA_URL = '/media/'
else:
    # En développement, utilisez les fichiers locaux
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')