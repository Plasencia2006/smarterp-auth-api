# Importar configuración base
from .base import *

# Determinar el entorno
import os
env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production' or os.environ.get('RAILWAY_ENVIRONMENT'):
    try:
        from .production import *
    except ImportError:
        pass
else:
    try:
        from .development import *
    except ImportError:
        pass

# Asegurar que DATABASES siempre exista
if 'DATABASES' not in dir():
    from .base import DATABASES