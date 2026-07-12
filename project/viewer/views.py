from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.files import File
from django.conf import settings
import json, zipfile, tempfile, os, shutil, logging

from .models import IRMImage, Annotation, Patient
from .forms import IRMUploadForm, IRMImageSearchForm, UploadIRMForm, PatientForm
from .utils import convert_dicom_to_png, validate_dicom_files
from accounts.models import CustomUser
from io import BytesIO
logger = logging.getLogger(__name__)

# ------------------------------- ACCUEIL --------------------------------

# ---------------------------- AUTHENTIFICATION ----------------------------
# viewer/views.py

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # --- DÉBUT DE LA LOGIQUE DE REDIRECTION ---
            if hasattr(user, 'role'): # Vérifie si l'attribut 'role' existe
                if user.role == 'superviseur':
                    return redirect('superviseur_dashboard')
                elif user.role == 'medecin':
                    return redirect('medecin_dashboard')
                elif user.role == 'radiologue':
                    return redirect('radiologue_dashboard')
            # Si l'utilisateur n'a pas de rôle ou pour les autres cas (ex: superadmin)
            return redirect('admin:index') # Redirige vers le panneau d'admin par défaut
            # --- FIN DE LA LOGIQUE DE REDIRECTION ---
        else:
            # Message d'erreur si l'authentification échoue
            return render(request, 'registration/login.html', {'error_message': 'Nom d’utilisateur ou mot de passe incorrect.'})
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# ----------------------------- UPLOAD SIMPLE -----------------------------
@login_required
def upload_irm(request):
    form = IRMUploadForm(request.POST, request.FILES)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'message': 'Upload réussi'})
            return redirect('home')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'errors': form.errors}, status=400)
    return render(request, 'viewer/upload.html', {'form': form})

# --------------------------- UPLOAD DICOM ZIP ----------------------------
@login_required
def upload_dicom(request):
    form = UploadIRMForm(request.POST, request.FILES)
    if request.method == 'POST' and form.is_valid():
        try:
            dicom_zip = request.FILES['dicom_zip']
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, dicom_zip.name)
                with open(zip_path, 'wb') as f:
                    for chunk in dicom_zip.chunks():
                        f.write(chunk)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                dicom_files = [
                    os.path.join(root, file)
                    for root, _, files in os.walk(temp_dir)
                    for file in files if file.lower().endswith(('.dcm', '.dicom'))
                ]

                if not dicom_files:
                    return JsonResponse({'success': False, 'error': 'Aucun fichier DICOM trouvé'})

                valid_files, _ = validate_dicom_files(dicom_files)
                if not valid_files:
                    return JsonResponse({'success': False, 'error': 'Aucun fichier DICOM valide'})

                output_dir = os.path.join(temp_dir, 'converted')
                os.makedirs(output_dir, exist_ok=True)
                png_paths = convert_dicom_to_png(valid_files, output_dir)

                for path in png_paths:
                    with open(path, 'rb') as f:
                        image = IRMImage(
                            patient_name=form.cleaned_data['patient_name'],
                            exam_date=form.cleaned_data['exam_date'],
                            avc_type=form.cleaned_data['avc_type'],
                        )
                        image.image.save(os.path.basename(path), File(f))
                        image.save()

            return JsonResponse({'success': True, 'message': f'{len(png_paths)} images converties'})
        except Exception as e:
            logger.error(f"Erreur lors du traitement DICOM : {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'viewer/upload.html', {'form': form})

# ----------------------------- DASHBOARDS PAR RÔLE -----------------------------
@user_passes_test(lambda u: u.role == 'superviseur')
def superviseur_dashboard(request):
    patients = Patient.objects.all()
    return render(request, 'superviseur/dashboard.html', {'patients': patients})

@user_passes_test(lambda u: u.role == 'medecin')
def medecin_dashboard(request):
    query = request.GET.get('q')
    patients = Patient.objects.filter(Q(nom__icontains=query) | Q(prenom__icontains=query)) if query else Patient.objects.all()
    return render(request, 'medecin/dashboard.html', {'patients': patients})

# viewer/views.py

# Dans viewer/views.py

# Assurez-vous que ces imports sont bien en haut de votre fichier
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Patient, IRMImage 
# ... etc ...


@user_passes_test(lambda u: u.role == 'radiologue')
def radiologue_dashboard(request):
    message = ''
    if request.method == 'POST':
        # 1. On récupère TOUTES les données du formulaire, y compris la date
        patient_id = request.POST.get('patient_id')
        exam_date = request.POST.get('exam_date')  # <-- C'est la ligne qui manquait
        irm_file = request.FILES.get('irm_file')

        try:
            patient_obj = Patient.objects.get(id=patient_id)
            
            # 2. On utilise TOUTES les données pour créer l'image dans la base de données
            IRMImage.objects.create(
                patient_name=f"{patient_obj.prenom} {patient_obj.nom}", 
                exam_date=exam_date,  # <-- On utilise la date ici
                image=irm_file
            )
            
            message = f"Image IRM ajoutée pour {patient_obj.nom}"
        except Patient.DoesNotExist:
            message = "Patient introuvable."
    
    # On envoie la liste des patients au template pour qu'elle s'affiche dans le menu déroulant
    patients = Patient.objects.all()
    
    return render(request, 'radiologue/dashboard.html', {
        'message': message,
        'patients': patients,
    })
# ----------------------------- PATIENTS -----------------------------
@user_passes_test(lambda u: u.role == 'superviseur')
def ajouter_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Le nouveau patient a été ajouté avec succès.")
            return redirect('superviseur_dashboard')
    else:
        form = PatientForm()
        
    # On utilise maintenant le nouveau template
    return render(request, 'superviseur/patient_form.html', {'form': form})

@user_passes_test(lambda u: u.role == 'superviseur')
def manage_patients(request):
    patients = Patient.objects.all()
    return render(request, 'dashboard/manage_patients.html', {'patients': patients})

# ----------------------------- AFFICHAGE IMAGE & ANNOTATION -----------------------------
@login_required
def view_image(request, image_id):
    image = get_object_or_404(IRMImage, id=image_id)
    return render(request, 'viewer/view_image.html', {'image': image})

@login_required
@csrf_exempt
def save_annotations(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_id = request.GET.get('image_id')
            image = IRMImage.objects.get(id=image_id)
            Annotation.objects.create(image=image, user=request.user, data=data.get('rectangles'))
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Erreur lors de l'annotation : {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)

# ----------------------------- RECHERCHE D'IMAGES -----------------------------
@login_required
def search_images(request):
    form = IRMImageSearchForm(request.GET or None)
    images = IRMImage.objects.all()
    if form.is_valid():
        data = form.cleaned_data
        if data.get('patient_name'):
            images = images.filter(patient_name__icontains=data['patient_name'])
        if data.get('exam_date'):
            images = images.filter(exam_date=data['exam_date'])
        if data.get('avc_type'):
            images = images.filter(avc_type=data['avc_type'])
    return render(request, 'viewer/search.html', {'form': form, 'images': images})

@user_passes_test(lambda u: u.role == 'medecin')
def medecin_patient_list(request):
    query = request.GET.get('q', '')
    if query:
        patients = Patient.objects.filter(
            Q(nom__icontains=query) |
            Q(prenom__icontains=query) |
            Q(cin__icontains=query)
        )
    else:
        patients = Patient.objects.all()
    return render(request, 'medecin/patient_list.html', {'patients': patients, 'query': query})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def superviseur_home(request):
    return render(request, 'viewer/superviseur_home.html')



from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def medecin_home(request):
    return render(request, 'viewer/medecin_home.html')



from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def radiologue_home(request):
    return render(request, 'viewer/radiologue_home.html')




from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def redirect_after_login(request):
    if request.user.groups.filter(name='Superviseur').exists():
        return redirect('superviseur_dashboard')
    elif request.user.groups.filter(name='Médecin').exists():
        return redirect('medecin_dashboard')
    elif request.user.groups.filter(name='Radiologue').exists():
        return redirect('radiologue_dashboard')
    else:
        return redirect('home')  # ou une page d’erreur personnalisée




# Dans viewer/views.py


# Assurez-vous d'importer les modèles nécessaires en haut du fichier
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Patient, IRMImage, Scan # <-- VÉRIFIEZ QUE 'Scan' EST IMPORTÉ

@login_required
def patient_detail(request, patient_id):
    # Cette ligne est correcte, elle récupère le patient
    patient = get_object_or_404(Patient, id=patient_id)
    
    # On garde la recherche pour les anciennes images (si besoin)
    # Note : cette méthode n'est pas fiable si deux patients ont le même nom
    irm_images = IRMImage.objects.filter(patient_name=f"{patient.prenom} {patient.nom}") 
    
    # --- SECTION AJOUTÉE POUR LA TÂCHE 1 ---
    # On récupère tous les scans 3D qui sont directement liés à ce patient via la ForeignKey
    scans = Scan.objects.filter(patient=patient)
    
    # On prépare le contexte avec toutes les données
    context = {
        'patient': patient,
        'irm_images': irm_images,
        'scans': scans, # <-- On envoie la liste des scans au template
    }
    
    return render(request, 'medecin/patient_detail.html', context)






# Dans viewer/views.py

# Assurez-vous d'avoir ces imports en haut du fichier
from django.http import HttpResponse
import io
import zipfile

# ... (vos autres vues) ...


@login_required
def download_report(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    try:
        rapport = patient.rapport
        contenu = rapport.contenu
    except Rapport.DoesNotExist:
        contenu = "Aucun rapport n'a été rédigé pour ce patient."

    # Crée une réponse HTTP avec le contenu du rapport en tant que fichier texte
    response = HttpResponse(contenu, content_type='text/plain; charset=utf-8')
    
    # Cet en-tête force le navigateur à télécharger le fichier
    response['Content-Disposition'] = f'attachment; filename="rapport_{patient.nom}_{patient.prenom}.txt"'
    
    return response


@login_required
def download_dossier(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Crée un buffer en mémoire pour ne pas avoir à créer de fichier temporaire sur le serveur
    buffer = io.BytesIO()
    
    # Crée le fichier ZIP dans le buffer
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Ajouter le rapport au ZIP
        try:
            if patient.rapport:
                zip_file.writestr('Rapport_Medical.txt', patient.rapport.contenu)
        except Rapport.DoesNotExist:
            pass # S'il n'y a pas de rapport, on ne fait rien

        # 2. Ajouter toutes les coupes 2D des scans NIfTI au ZIP
        scans = patient.scans.all()
        for scan in scans:
            # Crée un dossier dans le ZIP pour chaque scan
            dossier_scan = f'Scan_{scan.id}_{scan.date_scan.strftime("%Y-%m-%d")}/'
            for coupe in scan.coupes.all():
                # On s'assure que le fichier existe sur le disque
                if coupe.image and hasattr(coupe.image, 'path'):
                    chemin_fichier = coupe.image.path
                    # Nom du fichier à l'intérieur du ZIP
                    nom_archive = f'{dossier_scan}coupe_{coupe.numero_coupe}.png'
                    zip_file.write(chemin_fichier, nom_archive)

    # Prépare la réponse HTTP pour envoyer le ZIP
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="dossier_{patient.nom}_{patient.prenom}.zip"'
    
    return response








# Dans viewer/views.py
from .models import Rapport, IRMImage, Patient
from .forms import RapportForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

# ... vos autres vues ...

@login_required
def edit_report(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    # Essaye de trouver un rapport existant, sinon crée une nouvelle instance
    try:
        rapport = patient.rapport
    except Rapport.DoesNotExist:
        rapport = Rapport(patient=patient)

    if request.method == 'POST':
        form = RapportForm(request.POST, instance=rapport)
        if form.is_valid():
            rapport_sauvegarde = form.save(commit=False)
            rapport_sauvegarde.medecin = request.user
            rapport_sauvegarde.save()
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = RapportForm(instance=rapport)

    return render(request, 'medecin/edit_report.html', {
        'form': form,
        'patient': patient
    })

@login_required
def annotate_image(request, image_id):
    image = get_object_or_404(IRMImage, id=image_id)
    # La logique de sauvegarde des annotations (en JSON) peut être ajoutée ici via une requête POST
    return render(request, 'medecin/annotate_image.html', {'image': image})












# Dans viewer/views.py
# Imports nécessaires en haut du fichier
import nibabel as nib
import numpy as np
from PIL import Image as PilImage
from django.core.files.base import ContentFile

from .forms import ScanForm
from .models import Scan, Coupe

# Dans viewer/views.py

# ... (gardez tous vos autres imports) ...
# Importez le système de messages de Django
from django.contrib import messages

# viewer/views.py

# Assurez-vous d'avoir tous ces imports en haut de votre fichier
import zipfile
import tempfile
import traceback
from django.contrib import messages
from django.core.files.base import ContentFile
from io import BytesIO
import nibabel as nib
import numpy as np
from PIL import Image as PilImage
# ... et tous vos autres imports ...

@login_required
def upload_scan(request):
    if request.method == 'POST':
        form = ScanForm(request.POST, request.FILES)
        if form.is_valid():
            # On ne sauvegarde pas encore en base de données pour gérer le fichier d'abord
            scan_instance = form.save(commit=False) 
            
            uploaded_file = request.FILES['nifti_file']
            temp_dir = None # Pour le nettoyage des fichiers temporaires
            scan_was_saved = False # Un drapeau pour savoir si on doit supprimer en cas d'erreur

            try:
                # ÉTAPE 1: Gérer le cas où le fichier est un ZIP et extraire le NIfTI
                if uploaded_file.name.lower().endswith('.zip'):
                    temp_dir = tempfile.TemporaryDirectory()
                    zip_path = os.path.join(temp_dir.name, uploaded_file.name)
                    
                    with open(zip_path, 'wb+') as f:
                        for chunk in uploaded_file.chunks(): f.write(chunk)
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        nifti_files_in_zip = [f for f in zip_ref.namelist() if f.lower().endswith(('.nii', '.nii.gz'))]
                        if not nifti_files_in_zip:
                            raise ValueError("Aucun fichier NIfTI (.nii ou .nii.gz) trouvé dans l'archive ZIP.")
                        
                        # On extrait le premier fichier NIfTI trouvé
                        nifti_to_extract = nifti_files_in_zip[0]
                        zip_ref.extract(nifti_to_extract, path=temp_dir.name)
                        extracted_nifti_path = os.path.join(temp_dir.name, nifti_to_extract)
                        
                        # On attache le vrai fichier NIfTI à l'instance du scan et on sauvegarde
                        with open(extracted_nifti_path, 'rb') as f:
                            scan_instance.nifti_file.save(os.path.basename(extracted_nifti_path), File(f), save=True)
                        scan_was_saved = True

                else: # Le fichier est déjà un NIfTI, on peut le sauvegarder directement
                    scan_instance.save()
                    scan_was_saved = True
                
                # À ce stade, on est certain d'avoir un fichier NIfTI valide sauvegardé
                nifti_path = scan_instance.nifti_file.path

                # ÉTAPE 2: Traitement du fichier NIfTI pour créer les coupes 2D
                nifti_img = nib.load(nifti_path)
                nifti_data = nifti_img.get_fdata()

                if np.max(nifti_data) == 0:
                     raise ValueError("Les données du fichier NIfTI sont entièrement noires.")

                nifti_data = (nifti_data / np.max(nifti_data)) * 255.0
                nifti_data = nifti_data.astype(np.uint8)

                for i in range(nifti_data.shape[2]):
                    slice_data = np.rot90(nifti_data[:, :, i])
                    pil_img = PilImage.fromarray(slice_data, 'L')
                    buffer = BytesIO()
                    pil_img.save(buffer, format='PNG')
                    coupe = Coupe(scan=scan_instance, numero_coupe=i)
                    file_name = f'scan_{scan_instance.id}_slice_{i}.png'
                    coupe.image.save(file_name, ContentFile(buffer.getvalue()), save=True)
                
                messages.success(request, f"Le scan pour {scan_instance.patient} a été uploadé et traité avec succès !")
                return redirect('view_scan', scan_id=scan_instance.id)

            except Exception as e:
                # GESTION D'ERREUR : Affiche l'erreur, supprime l'objet en BDD et informe l'utilisateur
                traceback.print_exc() # Pour le débogage dans la console
                if scan_was_saved and scan_instance.pk:
                    scan_instance.delete() 
                messages.error(request, f"L'upload a échoué. Erreur : {e}")

            finally:
                # Nettoie le dossier temporaire s'il a été utilisé
                if temp_dir:
                    temp_dir.cleanup()

    else:
        form = ScanForm()
    
    return render(request, 'medecin/upload_scan.html', {'form': form})

# Dans viewer/views.py
@login_required
def view_scan(request, scan_id):
    scan = get_object_or_404(Scan, id=scan_id)
    # On récupère toutes les coupes liées à ce scan, elles sont déjà ordonnées
    coupes = scan.coupes.all()
    return render(request, 'medecin/view_scan.html', {'scan': scan, 'coupes': coupes})










# À la fin de viewer/views.py

@user_passes_test(lambda u: u.role == 'superviseur')
def edit_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f"Les informations du patient {patient.nom} {patient.prenom} ont été mises à jour.")
            return redirect('superviseur_dashboard')
    else:
        form = PatientForm(instance=patient)
    
    # On utilise le même template, mais en lui passant le patient existant
    return render(request, 'superviseur/patient_form.html', {'form': form, 'patient': patient})

@user_passes_test(lambda u: u.role == 'superviseur')
def delete_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    if request.method == 'POST':
        patient_name = f"{patient.nom} {patient.prenom}"
        patient.delete()
        messages.success(request, f"Le patient {patient_name} a été supprimé avec succès.")
        return redirect('superviseur_dashboard')
    
    # Si la méthode n'est pas POST, on redirige simplement
    return redirect('superviseur_dashboard')