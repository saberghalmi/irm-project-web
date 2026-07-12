from django import forms
from .models import IRMImage


# Formulaire upload direct (PNG, JPG, NIfTI, DICOM)
class IRMUploadForm(forms.ModelForm):
    class Meta:
        model = IRMImage
        fields = ['patient_name', 'exam_date', 'avc_type', 'image']

    def clean_image(self):
        file = self.cleaned_data.get('image')
        valid_extensions = ['.dcm', '.nii', '.nii.gz', '.png', '.jpg', '.jpeg']
        import os

        ext = os.path.splitext(file.name)[1].lower()
        if file.name.lower().endswith('.nii.gz'):
            ext = '.nii.gz'

        if ext not in valid_extensions:
            raise forms.ValidationError("Format non supporté. Formats acceptés : .dcm, .nii, .nii.gz, .png, .jpg")
        return file


# Formulaire recherche
class IRMImageSearchForm(forms.Form):
    patient_name = forms.CharField(required=False, label="Nom du patient")
    exam_date = forms.DateField(required=False, label="Date de l'examen", widget=forms.DateInput(attrs={'type': 'date'}))
    avc_type = forms.ChoiceField(
        required=False,
        label="Type d'AVC",
        choices=[('', '---'), ('ischémique', 'Ischémique'), ('hémorragique', 'Hémorragique')]
    )


# Formulaire upload ZIP de DICOMs
class UploadIRMForm(forms.Form):
    dicom_zip = forms.FileField(label="Archive DICOM (.zip)")
    patient_name = forms.CharField(label="Nom du patient")
    exam_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Date de l'examen")
    avc_type = forms.ChoiceField(
        choices=[
            ('ischémique', 'Ischémique'),
            ('hémorragique', 'Hémorragique'),
            ('inconnu', 'Inconnu'),
        ],
        label="Type d'AVC"
    )


from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'

# Dans viewer/forms.py
from django import forms
from .models import Rapport

class RapportForm(forms.ModelForm):
    class Meta:
        model = Rapport
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={'rows': 15, 'class': 'form-control'}),
        }















# Dans viewer/forms.py
from .models import Scan # Importez le nouveau modèle

# ... (gardez RapportForm) ...

class ScanForm(forms.ModelForm):
    class Meta:
        model = Scan
        fields = ['patient', 'nifti_file', 'description']