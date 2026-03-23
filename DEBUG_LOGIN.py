#!/usr/bin/env python
"""
Script de debug para test de login
Ejecutar: python DEBUG_LOGIN.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from creditos.models import Perfil

print("=" * 60)
print("DEBUG: Verificando Sistema de Login")
print("=" * 60)

# Verificar usuarios
print("\n1. Usuarios en la Base de Datos:")
usuarios = User.objects.all()
print(f"   Total de usuarios: {len(usuarios)}")
for u in usuarios:
    print(f"   - {u.username}")

# Verificar perfiles
print("\n2. Perfiles en la Base de Datos:")
perfiles = Perfil.objects.all()
print(f"   Total de perfiles: {len(perfiles)}")
for p in perfiles:
    print(f"   - {p.usuario.username}: {p.tipo}")

# Test de autenticación
print("\n3. Test de Autenticación:")
test_users = [('Est1', '1234'), ('profesor1', '1234')]

for username, password in test_users:
    print(f"\n   Probando {username}...")
    user = authenticate(username=username, password=password)
    if user:
        print(f"   ✓ Autenticación exitosa")
        try:
            print(f"   ✓ Perfil: {user.perfil.tipo}")
            print(f"   ✓ Créditos: {user.perfil.creditos}")
        except Exception as e:
            print(f"   ✗ Error al acceder a perfil: {e}")
    else:
        print(f"   ✗ Autenticación fallida")

print("\n" + "=" * 60)
