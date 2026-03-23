from django import forms
from django.contrib.auth.models import User
from .models import Envio, Revision


class LoginForm(forms.Form):
    """Formulario de login"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
        })
    )


class RectificacionForm(forms.ModelForm):
    """Formulario para enviar rectificación de ejercicio"""
    class Meta:
        model = Envio
        fields = ['descripcion', 'contexto_rectificacion', 'envio_corregido', 'documento_rectificacion']
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe la rectificación...',
            }),
            'contexto_rectificacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Contexto: ¿Qué estás rectificando?',
            }),
            'envio_corregido': forms.Select(attrs={
                'class': 'form-control',
            }),
            'documento_rectificacion': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
            }),
        }
        labels = {
            'descripcion': 'Descripción de la rectificación',
            'contexto_rectificacion': 'Contexto',
            'envio_corregido': '¿Qué envío estás corrigiendo? (opcional)',
            'documento_rectificacion': 'Adjuntar documento (opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Solo mostrar envíos aceptados o rechazados del usuario
            self.fields['envio_corregido'].queryset = Envio.objects.filter(
                estudiante=user,
                aceptado__in=[True, False]
            ).exclude(tipo='rectificacion').order_by('-fecha_envio')
        self.fields['contexto_rectificacion'].required = False
        self.fields['envio_corregido'].required = False
        self.fields['documento_rectificacion'].required = False


class EjercicioCPForm(forms.ModelForm):
    """Formulario para enviar ejercicio CP"""
    class Meta:
        model = Envio
        fields = ['numero_cp', 'numero_ejercicio', 'descripcion', 'pdf']
        widgets = {
            'numero_cp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: CP1, CP2, etc.',
            }),
            'numero_ejercicio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1.a, 1.b, 2.c, etc.',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del ejercicio (opcional)',
            }),
            'pdf': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf',
            }),
        }
        labels = {
            'numero_cp': 'Número de CP',
            'numero_ejercicio': 'Número de inciso/ejercicio',
            'descripcion': 'Descripción',
            'pdf': 'Archivo PDF',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = False
        self.fields['pdf'].required = False


class MemeForm(forms.ModelForm):
    """Formulario para enviar meme"""
    class Meta:
        model = Envio
        fields = ['descripcion', 'imagen']
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del meme (opcional)',
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }
        labels = {
            'descripcion': 'Descripción',
            'imagen': 'Imagen',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = False


class RevisionForm(forms.ModelForm):
    """Formulario para revisar y aceptar/rechazar envíos"""
    aceptado = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Aceptar este envío'
    )
    
    class Meta:
        model = Revision
        fields = ['aceptado', 'creditos_otorgados', 'comentarios']
        widgets = {
            'creditos_otorgados': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
            }),
            'comentarios': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Comentarios adicionales (opcional)',
            }),
        }
        labels = {
            'creditos_otorgados': 'Créditos a otorgar',
            'comentarios': 'Comentarios',
        }
    
    def __init__(self, *args, envio=None, valor_defecto=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.envio = envio
        
        # Establecer el valor inicial de créditos
        if valor_defecto > 0:
            self.fields['creditos_otorgados'].initial = valor_defecto
            self.fields['creditos_otorgados'].widget.attrs['placeholder'] = f'Valor por defecto: {valor_defecto}'
        else:
            self.fields['creditos_otorgados'].initial = 10000
            self.fields['creditos_otorgados'].widget.attrs['placeholder'] = 'Valor por defecto: 10000'
        
        # Hacer comentarios opcional
        self.fields['comentarios'].required = False
