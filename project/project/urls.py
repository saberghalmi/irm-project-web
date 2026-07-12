from django.contrib import admin
from django.urls import path, include

# --- IMPORTS À AJOUTER ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Vous pouvez garder cette ligne si vous utilisez les pages de reset de mot de passe etc.
    path('accounts/', include('django.contrib.auth.urls')),

    # Inclut toutes les URLs de votre application 'viewer' (login, dashboards, etc.)
    path('', include('viewer.urls')),
]

# --- LIGNES À AJOUTER À LA FIN ---
# Cette configuration est essentielle pour que le serveur de développement
# puisse trouver et envoyer les fichiers que vous uploadez (images, scans NIfTI).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)