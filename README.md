# SmartERP — API de Autenticación

API REST multi-tenant para el sistema ERP SmartERP, construida con Django REST Framework y JWT.

## Stack
- Python 3.12
- Django 4.2.9
- Django REST Framework 3.14
- SimpleJWT 5.3.1
- PyMySQL + MariaDB

## Instalación

```bash
git clone https://github.com/TU_USUARIO/smarterp-auth-api.git
cd smarterp-auth-api
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # configura tus variables
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Endpoints

| Método | URL | Descripción | Auth |
|--------|-----|-------------|------|
| POST | /api/v1/auth/register/ | Registro de usuario | No |
| POST | /api/v1/auth/login/ | Login, retorna JWT | No |
| POST | /api/v1/auth/token/refresh/ | Renueva access token | No |
| GET  | /api/v1/auth/me/ | Perfil del usuario | JWT |
| GET  | /api/v1/business/ | Lista negocios | JWT |
| POST | /api/v1/business/ | Crear negocio | JWT |
| POST | /api/v1/business/membership/assign/ | Asignar rol | JWT + X-Business-ID |
| GET  | /api/v1/business/membership/ | Ver membresías | JWT + X-Business-ID |

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores.

## Tests

Importa `SmartERP.postman_collection.json` en Postman y corre la colección completa.