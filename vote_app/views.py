# vote_app/views.py

import json
import os
from django.conf import settings
from django.http import JsonResponse, HttpResponse
import os
import json
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Profile, Candidate, ElectionState, Vote
from django.utils import timezone
from datetime import timedelta

# Méthodes utilitaires pour les choix dynamiques
def get_specialites_by_cycle(cycle):
    """Retourne les spécialités disponibles pour un cycle donné"""
    specialites = {
        'bts': Profile.SPECIALITE_BTS,
        'hnd': Profile.SPECIALITE_HND,
        'lipro': Profile.SPECIALITE_LICENCEPRO,
        'litech': Profile.SPECIALITE_LICENCETECH,
        'bachelor': Profile.SPECIALITE_BACHELOR,
        'master': Profile.SPECIALITE_MASTER,
        'ingenieur': Profile.SPECIALITE_INGENIEUR,
    }
    return specialites.get(cycle, [])

def get_niveaux_by_cycle(cycle):
    """Retourne les niveaux disponibles pour un cycle donné"""
    niveaux = {
        'bts': [1, 2],
        'hnd': [1, 2],

        'lipro': [3],
        'litech': [3],
        'bachelor': [3],

        'master': [4, 5],

        'ingenieur': [1, 2, 3, 4, 5],
    }
    return niveaux.get(cycle, [])

def get_cycle_options(request):
    """API pour récupérer les spécialités et niveaux par cycle"""
    cycle = request.GET.get('cycle')
    
    if not cycle:
        return JsonResponse({'error': 'Cycle non spécifié'}, status=400)
    
    specialites = get_specialites_by_cycle(cycle)

    if cycle != 'ingenieur':
        niveaux = get_niveaux_by_cycle(cycle)
        
        return JsonResponse({
            'specialites': specialites,
            'niveaux': niveaux
        })
    else:        
        return JsonResponse({
            'specialites': specialites,
            'niveaux12': [1, 2],
            'niveaux345': [3, 4, 5]
        })

# Vue pour servir la page HTML principale
def index(request):
    return render(request, 'vote_app/index.html')

# ===============================================
# FONCTIONS HELPER
# ===============================================

def is_user_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.is_admin

# Convertit un objet User/Profile en dictionnaire pour la réponse JSON
def user_to_dict(user):
    """Convertit un objet User/Profile en dictionnaire pour la réponse JSON."""
    if not hasattr(user, 'profile') and not is_user_admin(user):
        Profile.objects.create(user=user) # Crée un profil si manquant
    return {
        'id': user.id,
        'nom': user.last_name,
        'prenom': user.first_name,
        'matricule': user.username,
        'campus': user.profile.campus,
        'cycle': user.profile.cycle,
        'cycle_display': user.profile.get_cycle_display(),
        'specialite': user.profile.specialite,
        'niveau': user.profile.niveau,
        'telephone': user.profile.telephone,
        'photo_url': user.profile.photo.url if user.profile.photo else None,
        'recu_url': user.profile.recu.url if user.profile.recu else None,
        'status': user.profile.status,
        'has_voted': user.profile.has_voted,
        'is_admin': user.profile.is_admin,
    }

# ===============================================
# VUES API  electionStatusMessage
# ===============================================

@csrf_exempt # Enregistrement d'un nouvel étudiant
def register_view(request):
    if request.method == 'POST':
        data = request.POST
        if User.objects.filter(username=data['matricule']).exists():
            return JsonResponse({'error': 'Ce matricule est déjà utilisé.'}, status=400)

        try:
            # Crée l'utilisateur Django
            user = User.objects.create_user(
                username=data['matricule'],
                password=data['password'],
                first_name=data['nom'],
                last_name=data['prenom']
            )
            
            # Crée le profil associé
            Profile.objects.create(
                user=user,
                campus=data['campus'],
                cycle=data['cycle'],
                specialite=data['specialite'],
                niveau=data['niveau'],
                telephone=data.get('telephone', ''),
                photo=request.FILES.get('photo'),
                recu=request.FILES.get('recu')
            )
        except Exception as e:
            user.delete()  # Supprime l'utilisateur si le profil échoue
            return JsonResponse({'error': 'Problème lors de la création du profil. Connexion instable'}, status=400)
            
        
        return JsonResponse({'success': 'Inscription réussie ! Votre compte est en attente de validation.'})
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@csrf_exempt # Connection d'un utilisateur
def login_view(request):
    print("Connexion en cours demarrée.......")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            matricule = data.get('matricule')
            password = data.get('password')
            
            user = authenticate(username=matricule, password=password)
            if user is not None:
                # Générer un nouveau token de session
                profile, created = Profile.objects.get_or_create(user=user)
                
                print("profile.has_active_session : ", profile.has_active_session)
                # Vérifier s'il y a une session ACTIVE (non expirée)
                if profile.has_active_session and not profile.is_admin:
                    return JsonResponse({
                        'success': False,
                        'error': 'Compte déjà connecté sur un autre appareil. Déconnectez-vous d\'abord ou attendez que la session expire.'
                    }, status=400)
                
                # Générer nouveau token
                session_token = profile.generate_session_token()
                # Stocker dans la session Django
                request.session['session_token'] = session_token
                request.session['user_id'] = user.id

                # Mettre à jour l'activité
                profile.last_activity = timezone.now()
                profile.save(update_fields=['last_activity'])
                
                # Connecter l'utilisateur
                login(request, user)

                try:
                    return JsonResponse({
                        'success': True,
                        'user': user_to_dict(user),
                        'message': 'Connexion réussie'
                    })
                except Exception as e:
                    print("ereur de la sortie JsonResponse : ", e)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Matricule ou mot de passe incorrect'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur de connexion: {str(e)}'
            }, status=400)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

login_required # Deconnection d'un utilisateur
def logout_view(request):
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            profile.invalidate_session()
        except Profile.DoesNotExist:
            pass

        # Déconnecter Django
        #if(not is_user_admin(request.user)):
        from django.contrib.auth import logout
        logout(request)
        # Nettoyer la session
        request.session.flush()
        
        return JsonResponse({
            'success': True,
            'message': 'Déconnexion réussie'
        })

@login_required
def check_session_view(request):
    """Vérifie si un utilisateur est connecté et renvoie ses informations."""
    return JsonResponse(user_to_dict(request.user))

@login_required # Collecte des données à charger au demarrage de l'Application
def dashboard_data_view(request):
    """Renvoie toutes les données nécessaires pour le tableau de bord."""
    election = ElectionState.load()
    
    # Récupérer les candidats sans .values() pour avoir les objets complets
    candidates_queryset = Candidate.objects.all()
    
    # Sérialiser manuellement les candidats
    candidates = []
    for candidate in candidates_queryset:
        candidate_data = {
            'id': candidate.id,
            'nom': candidate.nom,
            'prenom': candidate.prenom,
            'cycle': candidate.cycle,
            'specialite': candidate.specialite,
            'niveau': candidate.niveau,
            'campus': candidate.campus,
            'slogan': candidate.slogan,
            'votes': candidate.votes,
            'bureau_color': candidate.bureau_color,
            'bureau_name': candidate.bureau_name,
            'photo_url': candidate.photo_url.url if candidate.photo_url else None,  # Convertir Cloudinary en URL string
            'programme_url': candidate.programme_url
        }
        
        # Ajouter les libellés
        candidate_data['cycle_display'] = candidate.get_cycle_display()
        candidate_data['specialite_display'] = candidate.specialite_display
        
        candidates.append(candidate_data)
    candidates.reverse()  # Pour afficher les plus récents en premier
    # Pour l'admin, on renvoie aussi les listes d'utilisateurs
    pending_users = []
    all_users = []
    if is_user_admin(request.user):
        pending_users = [user_to_dict(u) for u in User.objects.filter(profile__status='pending')]
        all_users = [user_to_dict(u) for u in User.objects.filter(profile__is_admin=False)]

    print("dashboard_data GOODDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")

    return JsonResponse({
        'user': user_to_dict(request.user),
        'election_status': election.status,
        'candidates': candidates,
        'pending_users': pending_users,
        'all_users': all_users,
    })

@csrf_exempt
@login_required # Processus d'enregistrement d'un vote
def vote_view(request):
    if request.method == 'POST':
        user_profile = request.user.profile
        election = ElectionState.load()

        if user_profile.has_voted:
            return JsonResponse({'error': 'Vous avez déjà voté.'}, status=403)
        if user_profile.status != 'validated':
            return JsonResponse({'error': 'Votre compte n\'est pas validé.'}, status=403)
        if election.status != 'active':
            return JsonResponse({'error': 'L\'élection n\'est pas active.'}, status=403)

        data = json.loads(request.body)
        candidate_id = data.get('candidate_id')

        try:
            candidate = Candidate.objects.get(id=candidate_id)
            candidate.votes += 1
            candidate.save()

            user_profile.has_voted = True
            user_profile.save()

            # Créer un vote
            vote = Vote.objects.create(
                profile=user_profile,
                candidate=candidate,
            )
            vote.save()

            return JsonResponse({'success': 'Vote enregistré !'})
        except Candidate.DoesNotExist:
            return JsonResponse({'error': 'Candidat non trouvé.'}, status=404)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

# ===============================================
# VUES API - ADMINISTRATION
# ===============================================
@csrf_exempt
@login_required  # Modifier le statut d'un etudiant et le supprimer aussi
def manage_user_status_view(request, user_id):
    if not is_user_admin(request.user):
        return JsonResponse({'error': 'Accès refusé.'}, status=403)
    
    try:
        user_to_manage = User.objects.get(id=user_id)
        profile_to_manage = user_to_manage.profile
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé.'}, status=404)

    if request.method == 'PUT': # Valider/Désactiver
        data = json.loads(request.body)
        new_status = data.get('status')
        if new_status in ['validated', 'pending']:
            profile_to_manage.status = new_status
            profile_to_manage.save()
            return JsonResponse(user_to_dict(user_to_manage))
        return JsonResponse({'error': 'Statut invalide.'}, status=400)
    
    if request.method == 'DELETE': # Supprimer
        user_to_manage.delete()
        profile_to_manage.delete()
        return JsonResponse({'success': 'Utilisateur supprimé.'})
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required  # Creation d'un nouveau candidat
def manage_candidates_view(request):
    print("manage_candidates_view")
    if not is_user_admin(request.user):
        return JsonResponse({'error': 'Accès refusé.'}, status=403)
    if request.method == 'POST':
        if request.content_type == 'multipart/form-data':
                # Traitement pour FormData (avec photo)
                nom = request.POST.get('nom')
                prenom = request.POST.get('prenom')
                cycle = request.POST.get('cycle')
                specialite = request.POST.get('specialite')
                niveau = request.POST.get('niveau')
                campus = request.POST.get('campus')
                slogan = request.POST.get('slogan')
                photo = request.FILES.get('photo')
                programmePDF = request.FILES.get('programmePDF')
                bureau_nom=request.POST.get('bureau_name')
                bureau_color=request.POST.get('bureau_color', '#3498db')
                
                # Valider les données obligatoires
                if not all([nom, prenom, cycle, specialite, niveau, slogan]):
                    return JsonResponse({'error': 'Tous les champs sont obligatoires.'}, status=400)
                
                # Créer le nom complet
                name = f"{prenom} {nom}"

                # Vérifier si le candidat existe déjà
                if Candidate.objects.filter(name=name).exists():
                    return JsonResponse({'error': 'Ce candidat existe déjà.'}, status=400)
                # Créer le candidat
                candidate = Candidate.objects.create(
                    nom=nom,
                    prenom=prenom,
                    name=name,
                    cycle=cycle,
                    specialite=specialite,
                    niveau=niveau,
                    campus=campus,
                    slogan=slogan,
                    photo_url = photo,
                    bureau_name=bureau_nom,
                    bureau_color=bureau_color,
                    programme_pdf=programmePDF,
                    
                )

                
        return JsonResponse({'success': 'Inscription réussie ! Votre compte est en attente de validation.'})
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@csrf_exempt
@login_required  # Suppression d'un nouveau candidat
def manage_candidate_detail_view(request, candidate_id):
    if not is_user_admin(request.user):
        return JsonResponse({'error': 'Accès refusé.'}, status=403)
    
    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        return JsonResponse({'error': 'Candidat non trouvé.'}, status=404)

    if request.method == 'DELETE':
        candidate.delete()
        return JsonResponse({'success': 'Candidat supprimé.'})

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@csrf_exempt
@login_required # Activer ou desactiver l'election
def manage_election_view(request):
    if not is_user_admin(request.user):
        return JsonResponse({'error': 'Accès refusé.'}, status=403)
    
    if request.method == 'PUT':
        data = json.loads(request.body)
        new_status = data.get('status')
        election = ElectionState.load()
        if new_status in ['pending', 'active', 'closed']:
            election.status = new_status
            election.save()
            return JsonResponse({'status': election.status})
        return JsonResponse({'error': 'Statut invalide.'}, status=400)
        
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@csrf_exempt
@login_required  # Réinitialisation de l'élection
def reset_election_view(request):
    if not is_user_admin(request.user):
        return JsonResponse({'error': 'Accès refusé.'}, status=403)
    
    if request.method == 'POST':
        try:
            # Réinitialiser tous les votes
            Candidate.objects.all().update(votes=0)
            
            # Réinitialiser le statut "a voté" pour tous les utilisateurs
            Profile.objects.all().update(has_voted=False)

            Vote.objects.all().delete()
            
            # Remettre l'élection en statut "pending"
            election = ElectionState.objects.first()
            election.status = 'pending'
            election.save()
            
            return JsonResponse({'success': 'Élection réinitialisée avec succès'})
            
        except Exception as e:
            return JsonResponse({'error': f'Erreur lors de la réinitialisation: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


