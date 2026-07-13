# 🩻 Plateforme d'analyse et de visualisation d'images IRM

Ce projet est une plateforme web développée avec Django permettant aux professionnels de santé (radiologues, médecins, superviseurs) de gérer, visualiser et annoter des images IRM (imagerie par résonance magnétique) de patients, avec un suivi médical centralisé.

## 📌 Contexte

Le diagnostic médical à partir d'images IRM nécessite des outils adaptés pour visualiser, annoter et partager les résultats entre professionnels de santé. Ce projet propose une solution web permettant de centraliser les scans, faciliter les échanges entre radiologues et médecins, et suivre le parcours de chaque patient — du dépôt du scan jusqu'au rapport final.

Développé dans le cadre de mon stage chez **Yebni Information et Communication**.

## 👥 Rôles utilisateurs

Le système repose sur trois profils avec des permissions distinctes :

- **Superviseur** — gestion des patients, création et modification des dossiers
- **Radiologue** — upload et annotation des scans IRM, tableau de bord dédié
- **Médecin** — consultation des scans annotés, gestion des rapports, suivi des patients

## 🗂️ Structure du dépôt

```
├── accounts/            # Gestion des utilisateurs et authentification
│   ├── models.py
│   ├── views.py
│   └── migrations/
├── viewer/               # Cœur métier de l'application
│   ├── models.py         # Patient, IrmImage, Rapport, Scan
│   ├── views.py
│   ├── forms.py
│   ├── decorators.py     # Contrôle d'accès par rôle
│   ├── signals.py
│   └── templates/
│       ├── medecin/
│       ├── radiologue/
│       ├── superviseur/
│       └── viewer/
├── project/              # Configuration Django (settings, urls)
├── manage.py
└── requirements.txt
```

## 🛠️ Stack technique

- **Backend** : Django (Python)
- **Base de données** : SQLite (développement)
- **Traitement d'images médicales** : DICOM
- **Frontend** : HTML, CSS, JavaScript, templates Django

## 🚀 Installation

### Prérequis
- Python 3.9+
- pip

### Étapes

```bash
# Cloner le dépôt
git clone https://github.com/saberghalmi/irm-project-web.git
cd irm-project-web

# Créer et activer l'environnement virtuel
python -m venv env
env\Scripts\activate      # Windows
source env/bin/activate   # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate

# Lancer le serveur
python manage.py runserver
```

L'application est ensuite accessible sur `http://127.0.0.1:8000/`.

## ✨ Fonctionnalités principales

- Authentification et gestion des rôles (superviseur / radiologue / médecin)
- Upload et visualisation de scans IRM
- Annotation d'images médicales
- Génération et édition de rapports médicaux
- Tableaux de bord dédiés par rôle
- Gestion complète des dossiers patients

## 📝 Notes importantes

- Ce projet a été développé à but pédagogique et professionnel dans un contexte de stage ; il ne doit pas être utilisé en environnement de production médical réel sans audit de sécurité et conformité aux réglementations sur les données de santé (RGPD, etc.).
- Les fichiers `db.sqlite3` et `media/` ne sont pas inclus dans le dépôt pour des raisons de confidentialité des données patients.

## ✍️ Auteur

**Saber Ghalmi**
Étudiant ingénieur en Génie Informatique Industrielle — ENET'COM Sfax
