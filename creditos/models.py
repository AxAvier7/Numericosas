from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Perfil(models.Model):
    """Perfil extendido del usuario para diferenciar estudiantes y profesores"""
    TIPO_USUARIO = [
        ('estudiante', 'Estudiante'),
        ('profesor', 'Profesor'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO)
    creditos = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        ordering = ['-creditos', 'usuario__username']
    
    def __str__(self):
        return f"{self.usuario.username} ({self.get_tipo_display()})"


class Envio(models.Model):
    """Modelo para los envíos de estudiantes"""
    TIPO_ENVIO = [
        ('rectificacion', 'Rectificación de Ejercicio'),
        ('cp', 'Ejercicio CP'),
        ('meme', 'Meme'),
    ]
    
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='envios')
    tipo = models.CharField(max_length=15, choices=TIPO_ENVIO)
    descripcion = models.TextField()  # Contexto o descripción general
    
    # Específico para rectificación
    contexto_rectificacion = models.TextField(blank=True, null=True)
    envio_corregido = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='rectificaciones')
    documento_rectificacion = models.FileField(upload_to='pdfs/', blank=True, null=True)
    
    # Específico para CP
    numero_cp = models.CharField(max_length=10, blank=True, null=True)
    numero_ejercicio = models.CharField(max_length=10, blank=True, null=True)
    pdf = models.FileField(upload_to='pdfs/', blank=True, null=True)
    
    # Específico para meme
    imagen = models.ImageField(upload_to='memes/', blank=True, null=True)
    
    fecha_envio = models.DateTimeField(auto_now_add=True)
    aceptado = models.BooleanField(null=True, default=None)  # None = pendiente, True = aceptado, False = rechazado
    creditos_otorgados = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        ordering = ['-fecha_envio']
    
    def __str__(self):
        return f"{self.estudiante.username} - {self.get_tipo_display()} ({self.fecha_envio.strftime('%d/%m/%Y')})"


class ValorCP(models.Model):
    """Valores por defecto para cada inciso de CP"""
    numero_cp = models.CharField(max_length=10)
    numero_inciso = models.CharField(max_length=10)
    valor_defecto = models.IntegerField(validators=[MinValueValidator(0)])
    
    class Meta:
        unique_together = ('numero_cp', 'numero_inciso')
        ordering = ['numero_cp', 'numero_inciso']
    
    def __str__(self):
        return f"CP {self.numero_cp} - Inciso {self.numero_inciso}: {self.valor_defecto} créditos"


class ValorPredeterminado(models.Model):
    """Valores predeterminados para cada tipo de envío"""
    TIPO_ENVIO = [
        ('rectificacion', 'Rectificación'),
        ('cp', 'CP'),
        ('meme', 'Meme'),
    ]
    
    tipo = models.CharField(max_length=15, choices=TIPO_ENVIO, unique=True)
    valor_defecto = models.IntegerField(validators=[MinValueValidator(0)])
    
    class Meta:
        ordering = ['tipo']
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.valor_defecto} créditos"


class Revision(models.Model):
    """Revisión de envíos por parte del profesor"""
    envio = models.OneToOneField(Envio, on_delete=models.CASCADE, related_name='revision')
    profesor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='revisiones_realizadas')
    aceptado = models.BooleanField()
    creditos_otorgados = models.IntegerField(validators=[MinValueValidator(0)])
    comentarios = models.TextField(blank=True, null=True)
    fecha_revision = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_revision']
    
    def __str__(self):
        estado = "Aceptado" if self.aceptado else "Rechazado"
        return f"{self.envio} - {estado} ({self.creditos_otorgados} créditos)"

