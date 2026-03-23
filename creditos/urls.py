from django.urls import path
from . import views

urlpatterns = [
    # Login
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Estudiante
    path('estudiante/', views.estudiante_inicio, name='estudiante_inicio'),
    path('estudiante/rectificacion/', views.enviar_rectificacion, name='enviar_rectificacion'),
    path('estudiante/cp/', views.enviar_cp, name='enviar_cp'),
    path('estudiante/meme/', views.enviar_meme, name='enviar_meme'),
    path('estudiante/historial/', views.historial_envios, name='historial_envios'),
    
    # Profesor
    path('profesor/', views.profesor_inicio, name='profesor_inicio'),
    path('profesor/revisar/<int:envio_id>/', views.revisar_envio, name='revisar_envio'),
    path('profesor/historial/', views.historial_revisiones, name='historial_revisiones'),
    path('profesor/ranking/', views.ranking_estudiantes, name='ranking_estudiantes'),
]
