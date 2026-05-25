# apps/backups/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from apps.authentication.permissions import IsSuperAdmin
import os
import subprocess
import glob
from datetime import datetime
from django.db import connection


class BackupViewSet(viewsets.ViewSet):
    """
    Gestión de backups de base de datos MySQL
    Solo accesible para Super Admins
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def list(self, request):
        """Listar backups existentes"""
        backup_dir = getattr(settings, 'BACKUP_DIR', '/tmp/backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Buscar archivos .sql
        backup_files = glob.glob(os.path.join(backup_dir, '*.sql'))
        
        backups = []
        for file_path in sorted(backup_files, key=os.path.getmtime, reverse=True):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)
            
            backups.append({
                'id': file_name.replace('.sql', ''),
                'name': file_name.replace('.sql', ''),
                'filename': file_name,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'created_at': datetime.fromtimestamp(file_mtime).isoformat(),
                'status': 'completed',
                'path': file_path,
            })
        
        return Response(backups)
    
    def create(self, request):
        """Crear nuevo backup"""
        backup_dir = getattr(settings, 'BACKUP_DIR', '/tmp/backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
        
        db_settings = settings.DATABASES['default']
        
        # Comando mysqldump
        cmd = [
            'mysqldump',
            f'--user={db_settings["USER"]}',
            f'--password={db_settings["PASSWORD"]}',
            f'--host={db_settings.get("HOST", "localhost")}',
            f'--port={db_settings.get("PORT", 3306)}',
            '--databases', db_settings['NAME'],
            f'--result-file={backup_file}',
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            
            return Response({
                'message': 'Backup creado exitosamente',
                'file': backup_file,
                'size_mb': round(os.path.getsize(backup_file) / (1024 * 1024), 2)
            }, status=status.HTTP_201_CREATED)
            
        except subprocess.CalledProcessError as e:
            return Response({
                'error': 'Error al crear backup',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except subprocess.TimeoutExpired:
            return Response({
                'error': 'Timeout al crear backup'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restaurar backup"""
        backup_dir = getattr(settings, 'BACKUP_DIR', '/tmp/backups')
        backup_file = os.path.join(backup_dir, f'{pk}.sql')
        
        if not os.path.exists(backup_file):
            return Response({
                'error': 'Archivo de backup no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        db_settings = settings.DATABASES['default']
        
        try:
            # Comando mysql restore
            subprocess.run(
                f"mysql -u{db_settings['USER']} -p{db_settings['PASSWORD']} "
                f"-h{db_settings.get('HOST', 'localhost')} "
                f"-P{db_settings.get('PORT', 3306)} "
                f"{db_settings['NAME']} < {backup_file}",
                shell=True,
                check=True,
                timeout=600
            )
            
            return Response({'message': 'Backup restaurado exitosamente'})
            
        except subprocess.CalledProcessError as e:
            return Response({
                'error': 'Error al restaurar backup',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, pk=None):
        """Eliminar backup"""
        backup_dir = getattr(settings, 'BACKUP_DIR', '/tmp/backups')
        backup_file = os.path.join(backup_dir, f'{pk}.sql')
        
        if os.path.exists(backup_file):
            os.remove(backup_file)
            return Response({'message': 'Backup eliminado'})
        
        return Response({'error': 'Archivo no encontrado'}, status=404)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descargar backup"""
        backup_dir = getattr(settings, 'BACKUP_DIR', '/tmp/backups')
        backup_file = os.path.join(backup_dir, f'{pk}.sql')
        
        if os.path.exists(backup_file):
            from django.http import FileResponse
            response = FileResponse(open(backup_file, 'rb'), as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{pk}.sql"'
            return response
        
        return Response({'error': 'Archivo no encontrado'}, status=404)