from .base import *

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Security settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Database configuration for production
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['ATOMIC_REQUESTS'] = False

# Static files configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware for production
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# REST Framework production settings
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='webmaster@localhost')

# Logging configuration for production
LOGGING['handlers']['file'] = {
    'level': 'INFO',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': '/var/log/bibliflow/django.log',
    'maxBytes': 10485760,  # 10MB
    'backupCount': 10,
    'formatter': 'verbose',
}
LOGGING['root']['handlers'] = ['console', 'file']

# Celery configuration for production
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = False
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# File upload handling in production
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB

# Cache configuration for production
CACHES['default']['OPTIONS'] = {
    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
    'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
    'CONNECTION_POOL_KWARGS': {
        'max_connections': 100,
        'retry_on_timeout': True,
    }
}

# Monitoring and error tracking
if env('SENTRY_DSN', default=None):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        send_default_pii=False,
        environment=env('SENTRY_ENVIRONMENT', default='production'),
    )

# Performance optimizations
TEMPLATES[0]['OPTIONS']['debug'] = False