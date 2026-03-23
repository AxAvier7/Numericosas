from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Perfil, Envio, Revision, ValorCP, ValorPredeterminado
from .forms import LoginForm, RectificacionForm, EjercicioCPForm, MemeForm, RevisionForm


# ==================== LOGIN ====================
def login_view(request):
    """Vista de login para estudiantes y profesores"""
    if request.user.is_authenticated:
        try:
            tipo = request.user.perfil.tipo
            if tipo == 'estudiante':
                return redirect('estudiante_inicio')
            elif tipo == 'profesor':
                return redirect('profesor_inicio')
        except:
            pass
        return redirect('admin:index')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                try:
                    tipo = user.perfil.tipo
                    if tipo == 'estudiante':
                        return redirect('estudiante_inicio')
                    elif tipo == 'profesor':
                        return redirect('profesor_inicio')
                except:
                    pass
                return redirect('admin:index')
            else:
                form.add_error(None, 'Usuario o contraseña incorrectos')
    else:
        form = LoginForm()
    
    return render(request, 'creditos/login.html', {'form': form})


def logout_view(request):
    """Logout del usuario"""
    logout(request)
    return redirect('login')


# ==================== VISTAS ESTUDIANTE ====================
@login_required(login_url='login')
def estudiante_inicio(request):
    """Vista principal del estudiante con sus créditos y ranking"""
    try:
        perfil = request.user.perfil
        if perfil.tipo != 'estudiante':
            return redirect('profesor_inicio')
    except:
        return redirect('login')
    
    # Obtener ranking de créditos
    ranking = Perfil.objects.filter(tipo='estudiante').order_by('-creditos', 'usuario__username')
    
    # Encontrar posición del usuario actual
    posicion_actual = None
    for idx, p in enumerate(ranking, 1):
        if p.usuario == request.user:
            posicion_actual = idx
            break
    
    # Preparar datos para mostrar ranking con contexto
    ranking_context = []
    if posicion_actual:
        inicio = max(0, posicion_actual - 3)
        fin = min(len(ranking), posicion_actual + 2)
        
        for idx in range(inicio, fin):
            p = ranking[idx]
            numero = idx + 1
            es_actual = p.usuario == request.user
            
            # Calcular diferencia con usuario actual
            diferencia = ranking[posicion_actual - 1].creditos - p.creditos
            
            ranking_context.append({
                'numero': numero,
                'nombre': '*' * len(p.usuario.username) if not es_actual else p.usuario.get_full_name() or p.usuario.username,
                'creditos': f"{p.creditos:,}".replace(',', ' '),
                'diferencia': diferencia,
                'es_actual': es_actual,
            })
    
    envios_pendientes = Envio.objects.filter(estudiante=request.user, aceptado=None).count()
    envios_aceptados = Envio.objects.filter(estudiante=request.user, aceptado=True).count()
    
    context = {
        'perfil': perfil,
        'ranking': ranking_context,
        'posicion_actual': posicion_actual,
        'total_estudiantes': len(ranking),
        'envios_pendientes': envios_pendientes,
        'envios_aceptados': envios_aceptados,
    }
    
    return render(request, 'creditos/estudiante_inicio.html', context)


@login_required(login_url='login')
def enviar_rectificacion(request):
    """Formulario para enviar rectificación de ejercicio"""
    try:
        perfil = request.user.perfil
        if perfil.tipo != 'estudiante':
            return redirect('profesor_inicio')
    except:
        return redirect('login')
    
    if request.method == 'POST':
        form = RectificacionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            envio = form.save(commit=False)
            envio.estudiante = request.user
            envio.tipo = 'rectificacion'
            envio.save()
            return redirect('estudiante_inicio')
    else:
        form = RectificacionForm(user=request.user)
    
    return render(request, 'creditos/enviar_rectificacion.html', {'form': form})


@login_required(login_url='login')
def enviar_cp(request):
    """Formulario para enviar ejercicio CP"""
    try:
        perfil = request.user.perfil
        if perfil.tipo != 'estudiante':
            return redirect('profesor_inicio')
    except:
        return redirect('login')
    
    if request.method == 'POST':
        form = EjercicioCPForm(request.POST, request.FILES)
        if form.is_valid():
            envio = form.save(commit=False)
            envio.estudiante = request.user
            envio.tipo = 'cp'
            envio.save()
            return redirect('estudiante_inicio')
    else:
        form = EjercicioCPForm()
    
    return render(request, 'creditos/enviar_cp.html', {'form': form})


@login_required(login_url='login')
def enviar_meme(request):
    """Formulario para enviar meme"""
    try:
        perfil = request.user.perfil
        if perfil.tipo != 'estudiante':
            return redirect('profesor_inicio')
    except:
        return redirect('login')
    
    if request.method == 'POST':
        form = MemeForm(request.POST, request.FILES)
        if form.is_valid():
            envio = form.save(commit=False)
            envio.estudiante = request.user
            envio.tipo = 'meme'
            envio.save()
            return redirect('estudiante_inicio')
    else:
        form = MemeForm()
    
    return render(request, 'creditos/enviar_meme.html', {'form': form})


@login_required(login_url='login')
def historial_envios(request):
    """Ver historial de envíos del estudiante"""
    try:
        perfil = request.user.perfil
        if perfil.tipo != 'estudiante':
            return redirect('profesor_inicio')
    except:
        return redirect('login')
    
    envios = Envio.objects.filter(estudiante=request.user)
    
    context = {
        'envios': envios,
    }
    
    return render(request, 'creditos/historial_envios.html', context)


# ==================== VISTAS PROFESOR ====================
@login_required(login_url='login')
def profesor_inicio(request):
    """Vista principal del profesor con lista de pendientes"""
    try:
        perfil = request.user.perfil
        if perfil.tipo != 'profesor':
            return redirect('estudiante_inicio')
    except:
        return redirect('login')
    
    # Obtener envíos pendientes
    envios_pendientes = Envio.objects.filter(aceptado=None).select_related('estudiante').order_by('-fecha_envio')
    
    # Agrupar por tipo
    rectificaciones = envios_pendientes.filter(tipo='rectificacion')
    ejercicios_cp = envios_pendientes.filter(tipo='cp')
    memes = envios_pendientes.filter(tipo='meme')
    
    context = {
        'total_pendientes': envios_pendientes.count(),
        'rectificaciones': rectificaciones,
        'ejercicios_cp': ejercicios_cp,
        'memes': memes,
    }
    
    return render(request, 'creditos/profesor_inicio.html', context)


@login_required(login_url='login')
def revisar_envio(request, envio_id):
    """Vista para revisar y aceptar/rechazar un envío"""
    try:
        perfil = request.user.perfil
        if perfil.tipo != 'profesor':
            return redirect('estudiante_inicio')
    except:
        return redirect('login')
    
    envio = get_object_or_404(Envio, id=envio_id)
    
    # Obtener valor por defecto según el tipo
    valor_defecto = 0
    if envio.tipo == 'cp':
        try:
            valor_cp = ValorCP.objects.get(numero_cp=envio.numero_cp, numero_inciso=envio.numero_ejercicio)
            valor_defecto = valor_cp.valor_defecto
        except ValorCP.DoesNotExist:
            pass
    else:
        try:
            valor_pred = ValorPredeterminado.objects.get(tipo=envio.tipo)
            valor_defecto = valor_pred.valor_defecto
        except ValorPredeterminado.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = RevisionForm(request.POST, envio=envio, valor_defecto=valor_defecto)
        if form.is_valid():
            revision = form.save(commit=False)
            revision.envio = envio
            revision.profesor = request.user
            revision.save()
            
            # Actualizar créditos del estudiante si fue aceptado
            if revision.aceptado:
                perfil_estudiante = envio.estudiante.perfil
                perfil_estudiante.creditos += revision.creditos_otorgados
                perfil_estudiante.save()
                
                # Actualizar el envío
                envio.aceptado = True
                envio.creditos_otorgados = revision.creditos_otorgados
                envio.save()
            else:
                # Rechazado
                envio.aceptado = False
                envio.creditos_otorgados = 0
                envio.save()
            
            return redirect('profesor_inicio')
    else:
        form = RevisionForm(envio=envio, valor_defecto=valor_defecto)
    
    context = {
        'envio': envio,
        'form': form,
        'valor_defecto': valor_defecto,
    }
    
    return render(request, 'creditos/revisar_envio.html', context)


@login_required(login_url='login')
def historial_revisiones(request):
    """Ver historial de revisiones realizadas por el profesor"""
    try:
        perfil = request.user.perfil
        if perfil.tipo != 'profesor':
            return redirect('estudiante_inicio')
    except:
        return redirect('login')
    
    revisiones = Revision.objects.filter(profesor=request.user).select_related('envio').order_by('-fecha_revision')
    
    context = {
        'revisiones': revisiones,
    }
    
    return render(request, 'creditos/historial_revisiones.html', context)


@login_required(login_url='login')
def ranking_estudiantes(request):
    """Vista para que profesores vean el ranking completo de estudiantes"""
    try:
        perfil = request.user.perfil
        if perfil.tipo != 'profesor':
            return redirect('estudiante_inicio')
    except:
        return redirect('login')
    
    # Obtener ranking completo de estudiantes
    ranking = Perfil.objects.filter(tipo='estudiante').order_by('-creditos', 'usuario__username')
    
    # Preparar datos para mostrar
    ranking_context = []
    for idx, p in enumerate(ranking, 1):
        ranking_context.append({
            'numero': idx,
            'nombre': p.usuario.get_full_name() or p.usuario.username,
            'creditos': f"{p.creditos:,}".replace(',', ' '),
        })
    
    context = {
        'ranking': ranking_context,
        'total_estudiantes': len(ranking),
    }
    
    return render(request, 'creditos/ranking_estudiantes.html', context)

