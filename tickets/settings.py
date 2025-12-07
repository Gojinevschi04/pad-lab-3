from pathlib import Path

import environ
from django.urls.base import reverse_lazy

env = environ.Env(
    DEBUG=(bool, False),
)
BASE_DIR = Path.cwd()

SECRET_KEY = env("DJANGO_SECRET_KEY", default="unsafe-default")
DEBUG = env.bool("DEBUG", default="True")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["tickets.localhost", "127.0.0.1"])

# Observability
ZIPKIN_ENDPOINT = env(
    "ZIPKIN_ENDPOINT",
    default="http://localhost:9411/api/v2/spans",
)
LOCAL_NODE_IPV_4 = env("LOCAL_NODE_IPV_4", default="127.0.0.1")

# OAuth
OAUTH2_JWKS_URL = env(
    "OAUTH2_JWKS_URL",
    default="http://localhost/application/o/tickets-app/jwks/",
)
OAUTH2_AUTHORIZATION_URL = env(
    "OAUTH2_AUTHORIZATION_URL",
    default="http://localhost/application/o/authorize/",
)
OAUTH2_TOKEN_URL = env(
    "OAUTH2_TOKEN_URL",
    default="http://localhost/application/o/token/",
)
OAUTH2_REDIRECT_URL = env(
    "OAUTH2_REDIRECT_URL", default="http://localhost:8000/api/oauth2-redirect.html"
)


# Celery
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL", default="redis://localhost:6379/1"
)  # to do - keep it redis://localhost:6379/1
CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND",
    default="redis://localhost:6379/1",
)
CELERY_ACCEPT_CONTENT = env.list("CELERY_ACCEPT_CONTENT", default=["json"])
CELERY_TASK_SERIALIZER = env("CELERY_TASK_SERIALIZER", default="json")
CELERY_RESULT_SERIALIZER = env("CELERY_RESULT_SERIALIZER", default="json")
CELERY_TIMEZONE = env("CELERY_TIMEZONE", default="UTC")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 180
CELERY_WORKER_SEND_TASK_EVENTS = True

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env("EMAIL_PORT", default="587")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default="True")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="annagojinevschi@gmail.com")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="xmkouumdmsbqwazw")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# MinIO
AWS_ACCESS_KEY_ID = env("MINIO_ACCESS_KEY", default="minioadmin")
AWS_SECRET_ACCESS_KEY = env("MINIO_SECRET_KEY", default="minioadmin")
AWS_STORAGE_BUCKET_NAME = env("MINIO_BUCKET_NAME", default="tickets-files")
AWS_S3_ENDPOINT_URL = env("MINIO_ENDPOINT", default="http://localhost:9000")
AWS_S3_FILE_OVERWRITE = env.bool("AWS_S3_FILE_OVERWRITE", default="True")
AWS_QUERYSTRING_AUTH = env.bool("AWS_QUERYSTRING_AUTH", default="True")

# Application definition
INSTALLED_APPS = [
    # Unfold for admin
    "unfold",
    #  STD_APPS
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # REMOTE_APPS
    "rest_framework",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "django_celery_beat",
    "storages",
    # LOCAL_APPS
    "tickets.core",
    "tickets.depot",
    "tickets.treasury",
    "tickets.ui",
    "tickets.debug",
]

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "location": "static",
            "custom_domain": env(
                "AWS_S3_CUSTOM_DOMAIN", default="localhost:9000/tickets-files"
            ),
            "url_protocol": env("AWS_S3_URL_PROTOCOL", default="http:"),
        },
    },
}

UNFOLD = {
    "SITE_TITLE": "Tickets Admin",
    "SITE_HEADER": "Admin Dashboard",
    "SHOW_COUNTS": True,
    "SIDEBAR": {
        "items": [
            {
                "label": "Statistics",
                "icon": "bar-chart-2",
                "url": "/admin/stats/",
            },
        ]
    },
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tickets.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tickets.wsgi.application"

REST_FRAMEWORK = {
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%SZ",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # "tickets.authentication.OpenIDAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES":
        (
            # "rest_framework.permissions.IsAuthenticated",
        ),
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Tickets API",
    "DESCRIPTION": "Seat availability, booking, validation",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "OAUTH2_REDIRECT_URL": OAUTH2_REDIRECT_URL,
    "OAUTH2_AUTHORIZATION_URL": OAUTH2_AUTHORIZATION_URL,
    "OAUTH2_TOKEN_URL": OAUTH2_TOKEN_URL,
    "SWAGGER_UI_SETTINGS": {
        "defaultModelRendering": "example",
        "docExpansion": "none",
        "defaultModelExpandDepth": "99",
        "filter": True,
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "displayRequestDuration": True,
    },
}

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS", default=["http://127.0.0.1:8000/", "http://localhost:9000/"]
)

CORS_ALLOW_ALL_ORIGINS = True

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="postgres"),
        "USER": env("POSTGRES_USER", default="postgres"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="postgres"),
        "HOST": env("POSTGRES_HOST", default="localhost"),  # to do - keep it localhost
        "PORT": env("POSTGRES_PORT", default="5432"),
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/static/"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = reverse_lazy("admin:login")

LOGIN_REDIRECT_URL = reverse_lazy("ui:home")

DEPOT_API_URL = env("DEPOT_API_URL", default="http://depot-service:8000/api")
DEPOT_API_TIMEOUT = env("TREASURY_API_TIMEOUT", default=10)

DEPOT = {
    "backend": "tickets.depot.backends.json.JsonDepotBackend",
    # "backend": "tickets.depot.back/ends.service.DepotServiceBackend",
    # "options": {
    #     "base_url": DEPOT_API_URL,
    #     "timeout": DEPOT_API_TIMEOUT,
    # },
}

TREASURY_API_URL = env("TREASURY_API_URL", default="http://treasury-api:8001/api")
TREASURY_API_KEY = env("TREASURY_API_KEY", default="treasury-key")
TREASURY_API_TIMEOUT = env("TREASURY_API_TIMEOUT", default=10)

TREASURY = {
    "backend": "tickets.treasury.backends.service.TreasuryServiceBackend",
    "options": {
        "base_url": TREASURY_API_URL,
        # "api_key": TREASURY_API_KEY,
        "timeout": TREASURY_API_TIMEOUT,
    },
}
