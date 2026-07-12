import os
import SimpleITK as sitk
import matplotlib.pyplot as plt
from django.conf import settings
from django.core.files import File
from io import BytesIO
from django.db import models

# ==============================================================================
# MODÈLE POUR LES PATIENTS
# ==============================================================================
class Patient(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    genre = models.CharField(max_length=10, choices=[('Homme', 'Homme'), ('Femme', 'Femme')])
    telephone = models.CharField(max_length=15, blank=True)
    adresse = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"


# ==============================================================================
# ANCIEN MODÈLE POUR LES IMAGES 2D (système original)
# ==============================================================================
def upload_to_irm(instance, filename):
    return os.path.join('irm_files', filename)

class IRMImage(models.Model):
    AVC_TYPES = [
        ('ischémique', 'Ischémique'),
        ('hémorragique', 'Hémorragique'),
        ('inconnu', 'Inconnu'),
    ]

    patient_name = models.CharField(max_length=100)
    exam_date = models.DateField()
    avc_type = models.CharField(max_length=20, choices=AVC_TYPES, blank=True)
    image = models.FileField(upload_to=upload_to_irm)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    png_preview = models.ImageField(upload_to='irm_previews/', blank=True, null=True)

    def __str__(self):
        return f"{self.patient_name} ({self.exam_date})"

    def save(self, *args, **kwargs):
        # On ne génère le preview que s'il n'existe pas déjà et si un fichier est présent
        generate_preview = bool(self.image and not self.png_preview)

        # On sauvegarde une première fois pour s'assurer que l'objet a un ID et un chemin de fichier
        super().save(*args, **kwargs)

        if generate_preview:
            try:
                image_path = self.image.path
                sitk_image = sitk.ReadImage(image_path)
                array = sitk.GetArrayFromImage(sitk_image)
                mid_slice = array[array.shape[0] // 2]  # coupe médiane

                fig, ax = plt.subplots(figsize=(6, 6))
                ax.imshow(mid_slice, cmap='gray')
                ax.axis('off')

                buf = BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
                buf.seek(0)
                plt.close(fig)

                png_name = os.path.splitext(os.path.basename(self.image.name))[0] + '_preview.png'
                self.png_preview.save(png_name, File(buf), save=False)

                # On sauvegarde une deuxième fois UNIQUEMENT pour mettre à jour le champ du preview
                super().save(update_fields=['png_preview'])

            except Exception as e:
                print(f"Erreur lors de la génération de l'aperçu PNG pour {self.image.name}: {e}")


# ==============================================================================
# MODÈLE POUR LES ANNOTATIONS SUR LES IMAGES 2D
# ==============================================================================
class Annotation(models.Model):
    image = models.ForeignKey(IRMImage, on_delete=models.CASCADE, related_name='annotations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Annotation de {self.user} sur {self.image}"


# ==============================================================================
# MODÈLE POUR LES RAPPORTS MÉDICAUX
# ==============================================================================
class Rapport(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='rapport')
    medecin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rapport pour {self.patient.nom} {self.patient.prenom}"


# ==============================================================================
# NOUVEAUX MODÈLES POUR LES SCANS 3D NIFTI
# ==============================================================================
class Scan(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='scans')
    date_scan = models.DateTimeField(auto_now_add=True)
    nifti_file = models.FileField(upload_to='nifti_scans/')
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Scan pour {self.patient} du {self.date_scan.strftime('%Y-%m-%d')}"

class Coupe(models.Model):
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name='coupes')
    image = models.ImageField(upload_to='slices/')
    numero_coupe = models.IntegerField()

    class Meta:
        ordering = ['numero_coupe']

    def __str__(self):
        return f"Coupe {self.numero_coupe} du {self.scan}"