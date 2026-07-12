
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# On définit une classe pour personnaliser l'affichage dans l'admin
class CustomUserAdmin(UserAdmin):
    # Ajoute le champ 'role' à la liste des champs affichés dans la liste des utilisateurs
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    
    # Ajoute le champ 'role' aux formulaires de création et d'édition d'utilisateur
    # On reprend les fieldsets de base de UserAdmin et on ajoute notre champ
    fieldsets = UserAdmin.fieldsets + (
        ('Rôle personnalisé', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Rôle personnalisé', {'fields': ('role',)}),
    )

# On enregistre le modèle CustomUser avec sa configuration personnalisée
admin.site.register(CustomUser, CustomUserAdmin)