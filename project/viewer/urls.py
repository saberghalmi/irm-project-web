from django.urls import path
from .views import (
    
    login_view,
    logout_view,
    upload_irm,
    upload_dicom,
    view_image,
    search_images,
    save_annotations,
    manage_patients,
    medecin_patient_list,
    radiologue_dashboard,
    superviseur_home,
    medecin_home,
    radiologue_home,
    redirect_after_login,
    medecin_dashboard,
    ajouter_patient,
    patient_detail,
    edit_report,
    annotate_image,
    upload_scan,
    view_scan,
     download_report,
    download_dossier,
     edit_patient,
    delete_patient,

)

urlpatterns = [
     path('', login_view, name='home'), 
     path('patient/ajouter/', ajouter_patient, name='add_patient'),

    
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('upload/irm/', upload_irm, name='upload_irm'),
    path('upload/dicom/', upload_dicom, name='upload_dicom'),
    path('image/<int:image_id>/', view_image, name='view_image'),
    path('save_annotations/', save_annotations, name='save_annotations'),
    path('search/', search_images, name='search_images'),

    # Dashboards selon les rôles
    path('superviseur/dashboard/', manage_patients, name='superviseur_dashboard'),
   path('medecin/dashboard/', medecin_dashboard, name='medecin_dashboard'), 
    path('radiologue/dashboard/', radiologue_dashboard, name='radiologue_dashboard'),

    # Accès directs aux home des rôles
    path('superviseur/', superviseur_home, name='superviseur_home'),
    path('medecin/', medecin_home, name='medecin_home'),
    path('radiologue/', radiologue_home, name='radiologue_home'),
    path('medecin/patients/', medecin_patient_list, name='medecin_patient_list'),




    path('redirect-after-login/', redirect_after_login, name='redirect_after_login'),
     path('patient/<int:patient_id>/', patient_detail, name='patient_detail'),
     path('patient/<int:patient_id>/report/', edit_report, name='edit_report'),
    path('image/<int:image_id>/annotate/', annotate_image, name='annotate_image'),
     path('upload-scan/', upload_scan, name='upload_scan'),
    path('scan/<int:scan_id>/', view_scan, name='view_scan'),
    path('report/<int:patient_id>/download/', download_report, name='download_report'),
    path('patient/<int:patient_id>/download-dossier/', download_dossier, name='download_dossier'),
     path('patient/<int:patient_id>/edit/', edit_patient, name='edit_patient'),
    path('patient/<int:patient_id>/delete/', delete_patient, name='delete_patient'),
]

