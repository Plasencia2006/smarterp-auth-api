import os
import sys


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Activa el entorno virtual."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()