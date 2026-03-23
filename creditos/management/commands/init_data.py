from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from creditos.models import Perfil, ValorCP


class Command(BaseCommand):
    help = 'Inicializa datos de prueba para el sistema de créditos'

    def handle(self, *args, **options):
        # Crear usuarios de prueba si no existen
        
        # Profesor
        if not User.objects.filter(username='profesor1').exists():
            profesor = User.objects.create_user(
                username='profesor1',
                password='1234',
                first_name='Juan',
                last_name='García',
                email='profesor@example.com'
            )
            Perfil.objects.create(usuario=profesor, tipo='profesor', creditos=0)
            self.stdout.write(self.style.SUCCESS('✅ Profesor creado: profesor1 / 1234'))

        # Estudiantes
        estudiantes = [
            ('Est1', 'Carlos', 'Rodríguez'),
            ('Est2', 'María', 'López'),
            ('Est3', 'Pedro', 'Martínez'),
            ('Est4', 'Laura', 'Sánchez'),
            ('Est5', 'Juan', 'Fernández'),
        ]

        for username, nombre, apellido in estudiantes:
            if not User.objects.filter(username=username).exists():
                estudiante = User.objects.create_user(
                    username=username,
                    password='1234',
                    first_name=nombre,
                    last_name=apellido,
                    email=f'{username}@example.com'
                )
                Perfil.objects.create(usuario=estudiante, tipo='estudiante', creditos=0)
                self.stdout.write(self.style.SUCCESS(f'✅ Estudiante creado: {username} / 1234'))

        # Crear valores por defecto para CP
        cp_valores = [
            ('CP1', '1.a', 25),
            ('CP1', '1.b', 25),
            ('CP1', '2.a', 30),
            ('CP1', '2.b', 20),
            ('CP2', '1.a', 35),
            ('CP2', '1.b', 35),
            ('CP2', '2.a', 30),
        ]

        for numero_cp, numero_inciso, valor in cp_valores:
            if not ValorCP.objects.filter(numero_cp=numero_cp, numero_inciso=numero_inciso).exists():
                ValorCP.objects.create(
                    numero_cp=numero_cp,
                    numero_inciso=numero_inciso,
                    valor_defecto=valor
                )

        self.stdout.write(self.style.SUCCESS('✅ Datos de prueba inicializados correctamente'))
