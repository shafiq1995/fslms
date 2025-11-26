import os
from pathlib import Path
import django_heroku
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'change-me')
DEBUG = True
ALLOWED_HOSTS = ['fslms.herokuapp.com', 'localhost', ]
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Project apps
    'apps.accounts',
    'apps.courses',
    # 'apps.enrollments',  # keep commented until you really use it
    'apps.payments',
    'apps.certificates',
    'apps.blog',
    'apps.admin_tools',
    'apps.core',
    'apps.home',
    'apps.instructor_tool',
    'apps.student_tool',
    'apps.faq',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
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
                'django.template.context_processors.static',
                'apps.core.context_processors.user_role_context',
            ],
        },
    },
]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3'}}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'your_database_name',  # Replace with your PostgreSQL database name
#         'USER': 'your_database_user',  # Replace with your PostgreSQL username
#         'PASSWORD': 'your_database_password',  # Replace with your PostgreSQL password
#         'HOST': 'localhost',  # Or the hostname/IP of your PostgreSQL server
#         'PORT': '5432',  # Default PostgreSQL port, change if different
#     }
# }
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', 'English'),
    ('bn', 'Bangla'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR,'static')
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
AUTH_USER_MODEL = 'accounts.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "futureskill100@gmail.com"

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:profile_redirect"
LOGOUT_REDIRECT_URL = "accounts:login"


STATICFILES_DIRS = [os.path.join(BASE_DIR,'src/static')
]


STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
django_heroku.settings(locals())


if 'DYNO' in os.environ:
    import django_heroku
    django_heroku.settings(locals())