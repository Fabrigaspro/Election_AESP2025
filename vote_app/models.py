# vote_app/models.py

from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from cloudinary.uploader import destroy
from django.utils import timezone
from datetime import timedelta

# Modèle pour étendre le modèle User de base de Django avec nos champs personnalisés
class Profile(models.Model):

    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('student', 'Étudiant'),
    ]
    # Statuts possibles pour un utilisateur
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté'),
    ]
    
    # Cycles disponibles
    CYCLE_CHOICES = [
        ('bts', 'BTS'),
        ('licence', 'Licence'),
        ('master', 'Master'),
        ('ingenieur', 'Ingénieur'),
    ]

    # Spécialités par cycle
    SPECIALITE_BTS = [
        ('IIA', 'Informatique Industriele et Automatisme'),
        ('ET', 'ElectroTechnique'),
        ('RES', 'Réseau et sécurité'),
        ('GL', 'Génie Logiciel'),
    ]

    SPECIALITE_LICENCE = [
        ('IIA', 'Informatique Industriele et Automatisme'),
        ('ET', 'ElectroTechnique'),
        ('RES', 'Réseau et sécurité'),
        ('GL', 'Génie Logiciel'),
    ]

    SPECIALITE_MASTER = [
        ('IIA', 'Informatique Industriele et Automatisme'),
        ('ET', 'ElectroTechnique'),
        ('RES', 'Réseau et sécurité'),
        ('GL', 'Génie Logiciel'),
    ]

    SPECIALITE_INGENIEUR = [
        ('Prépa', 'Classe Preparatoire'),
        ('GCE', 'Génie Civil'),
        ('GESI', 'Génie Électrique et Systèmes Intélligents'),
        ('GM', 'Génie Mécanique'),
        ('GMA', 'Génie Mécatronique et Antomobile'),
        ('GIT', 'Génie Informatique et Télécommunication'),
        ('QHSE', 'Qualité Higiène Sécurité Environnement'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricule = models.CharField(max_length=100, default='MAT')
    cycle = models.CharField(max_length=100, choices=CYCLE_CHOICES, default='bts')
    specialite = models.CharField(max_length=100, blank=True, null=True)
    niveau = models.IntegerField(blank=True)
    photo = CloudinaryField('image', folder='photos/')
    recu = CloudinaryField('image', folder='recus/')
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    has_voted = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_connected = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)

    def is_actually_connected(self):
        """Vérifie si l'utilisateur est vraiment connecté"""
        if not self.is_connected:
            return False
    def update_activity(self):
        """Met à jour le timestamp d'activité"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
        
        # Considérer comme déconnecté après 30 minutes d'inactivité
        timeout = timezone.now() - timedelta(minutes=10)
        return self.last_activity > timeout

    def save(self, *args, **kwargs):
        """Sauvegarde le profil avec gestion sécurisée des images Cloudinary"""
        
        # Initialiser les variables pour suivre les changements
        old_photo_public_id = None
        old_recu_public_id = None
        
        # Si c'est une mise à jour (objet existant)
        if self.pk:
            try:
                old_instance = Profile.objects.get(pk=self.pk)
                
                # Vérifier si la photo a changé
                if (old_instance.photo and 
                    self.photo and 
                    hasattr(old_instance.photo, 'public_id') and
                    hasattr(self.photo, 'public_id') and
                    old_instance.photo.public_id != self.photo.public_id):
                    old_photo_public_id = old_instance.photo.public_id
                
                # Vérifier si le reçu a changé 
                if (hasattr(old_instance, 'recu') and old_instance.recu and 
                    hasattr(self, 'recu') and self.recu and
                    hasattr(old_instance.recu, 'public_id') and
                    hasattr(self.recu, 'public_id') and
                    old_instance.recu.public_id != self.recu.public_id):
                    old_recu_public_id = old_instance.recu.public_id
                    
            except Profile.DoesNotExist:
                pass
        self.matricule = self.user.username
        # Sauvegarder d'abord l'objet
        super().save(*args, **kwargs)  
        # Supprimer les anciennes images APRÈS la sauvegarde
        try:
            if old_photo_public_id:
                destroy(old_photo_public_id)
                print(f"✅ Ancienne photo supprimée: {old_photo_public_id}")
                
            if old_recu_public_id:
                destroy(old_recu_public_id)
                print(f"✅ Ancien reçu supprimé: {old_recu_public_id}")
                
        except Exception as e:
            print(f"⚠️ Erreur lors de la suppression des anciennes images: {e}")
    
    def delete(self, *args, **kwargs):
        """Supprime l'image Cloudinary lors de la suppression de l'objet"""
        try:
            # Vérifier si l'image existe et a un public_id
            if self.photo and hasattr(self.photo, 'public_id'):
                public_id = self.photo.public_id
                if public_id:
                    destroy(public_id)
                    print(f"✅ Image Cloudinary supprimée: {public_id}")
            if self.recu and hasattr(self.recu, 'public_id'):
                public_id = self.recu.public_id
                if public_id:
                    destroy(public_id)
                    print(f"✅ Image Cloudinary supprimée: {public_id}")
        except Exception as e:
            print(f"⚠️ Erreur lors de la suppression de l'image Cloudinary: {e}")
        
        # Toujours appeler super().delete() même en cas d'erreur
        super().delete(*args, **kwargs)

    def get_fullname(self):
        return f'{self.user.first_name} {self.user.last_name}'
    
    # Méthode pour obtenir les spécialités disponibles selon le cycle
    def get_available_specialites(self):
        if self.cycle == 'bts':
            return self.SPECIALITE_BTS
        elif self.cycle == 'licence':
            return self.SPECIALITE_LICENCE
        elif self.cycle == 'master':
            return self.SPECIALITE_MASTER
        elif self.cycle == 'ingenieur':
            return self.SPECIALITE_INGENIEUR
        return []

    def get_cycle_display(self):
        for code, name in self.CYCLE_CHOICES:
            if code == self.cycle:
                return name
        return self.cycle

    # Propriété pour afficher le libellé de la spécialité
    @property
    def specialite_display(self):
        specialites_dict = dict(
            self.SPECIALITE_BTS + 
            self.SPECIALITE_LICENCE + 
            self.SPECIALITE_MASTER + 
            self.SPECIALITE_INGENIEUR
        )
        print(specialites_dict)
        print(specialites_dict.get(self.specialite, self.specialite))
        return specialites_dict.get(self.specialite, self.specialite)

    def __str__(self):
        return f"Profil de {self.user.username}"

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"
    
    def __str__(self):
        return f"Profil de {self.user.username}"

# Modèle pour les candidats ou les listes
class Candidate(models.Model):

    # Cycles disponibles
    CYCLE_CHOICES = [
        ('bts', 'BTS'),
        ('licence', 'Licence'),
        ('master', 'Master'),
        ('ingenieur', 'Ingénieur'),
    ]

    # Spécialités par cycle
    SPECIALITE_BTS = [
        ('IIA', 'Informatique Industriele et Automatisme'),
        ('ET', 'ElectroTechnique'),
        ('RES', 'Réseau et sécurité'),
        ('GL', 'Génie Logiciel'),
    ]

    SPECIALITE_LICENCE = [
        ('IIA', 'Informatique Industriele et Automatisme'),
        ('ET', 'ElectroTechnique'),
        ('RES', 'Réseau et sécurité'),
        ('GL', 'Génie Logiciel'),
    ]

    SPECIALITE_MASTER = [
        ('IIA', 'Informatique Industriele et Automatisme'),
        ('ET', 'ElectroTechnique'),
        ('RES', 'Réseau et sécurité'),
        ('GL', 'Génie Logiciel'),
    ]

    SPECIALITE_INGENIEUR = [
        ('Prepa', 'Classe Preparatoire'),
        ('GCE', 'Génie Civil'),
        ('GESI', 'Génie Électrique et Systèmes Intélligents'),
        ('GM', 'Génie Mécanique'),
        ('GMA', 'Génie Mécatronique et Antomobile'),
        ('GIT', 'Génie Informatique et Télécommunication'),
        ('QHSE', 'Qualité Higiène Sécurité Environnement'),
    ]

    # Informations personnelles
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    name = models.CharField(max_length=200, unique=True)  # Nom complet
    
    # Informations académiques
    cycle = models.CharField(max_length=100, choices=CYCLE_CHOICES, default='bts')
    specialite = models.CharField(max_length=100)
    niveau = models.CharField(max_length=50)
    
    # Campagne
    slogan = models.TextField()
    photo_url = CloudinaryField('image', folder='candidats/')
    
    # Statistiques
    votes = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # NOUVEAUX CHAMPS POUR LE BUREAU
    bureau_name = models.CharField(
        max_length=100, 
        default='Bureau Exécutif',
        verbose_name='Nom du Bureau'
    )
    bureau_color = models.CharField(
        max_length=7,  # Format hex: #FFFFFF
        default='#3498db',
        verbose_name='Couleur du Bureau'
    )

    def save(self, *args, **kwargs):
        # Générer automatiquement le name complet
        if not self.name and self.prenom and self.nom:
            self.name = f"{self.prenom} {self.nom}"
        
        # Initialiser les variables pour suivre les changements
        old_photo_public_id = None

        # Si c'est une mise à jour (objet existant)
        if self.pk:
            try:
                old_instance = Candidate.objects.get(pk=self.pk)
                
                # Vérifier si la photo a changé
                if (old_instance.photo_url and 
                    self.photo_url and 
                    hasattr(old_instance.photo_url, 'public_id') and
                    hasattr(self.photo_url, 'public_id') and
                    old_instance.photo_url.public_id != self.photo_url.public_id):
                    old_photo_public_id = old_instance.photo_url.public_id
                    
            except Profile.DoesNotExist:
                pass
        # Sauvegarder d'abord l'objet
        super().save(*args, **kwargs)  
        # Supprimer les anciennes images APRÈS la sauvegarde
        try:
            if old_photo_public_id:
                destroy(old_photo_public_id)
                print(f"✅ Ancienne photo supprimée: {old_photo_public_id}")
        except Exception as e:
            print(f"⚠️ Erreur lors de la suppression des anciennes images: {e}")
    
    def delete(self, *args, **kwargs):
        """Supprime l'image Cloudinary lors de la suppression de l'objet"""
        try:
            # Vérifier si l'image existe et a un public_id
            if self.photo_url and hasattr(self.photo_url, 'public_id'):
                public_id = self.photo_url.public_id
                if public_id:
                    destroy(public_id)
                    print(f"✅ Image Cloudinary supprimée: {public_id}")
        except Exception as e:
            print(f"⚠️ Erreur lors de la suppression de l'image Cloudinary: {e}")
        
        # Toujours appeler super().delete() même en cas d'erreur
        super().delete(*args, **kwargs)
    def __str__(self):
        return self.name
    @property
    def photo_link(self):
        if self.photo_url:
            return self.photo_url.url
        return None

    def get_cycle_display(self):
        return dict(self.CYCLE_CHOICES).get(self.cycle, self.cycle)

    # Propriété pour afficher le libellé de la spécialité
    @property
    def specialite_display(self):
        specialites_dict = dict(
            self.SPECIALITE_BTS + 
            self.SPECIALITE_LICENCE + 
            self.SPECIALITE_MASTER + 
            self.SPECIALITE_INGENIEUR
        )
        return specialites_dict.get(self.specialite, self.specialite)
    # Propriété pour afficher le libellé du niveau
    @property
    def niveau_display(self):
        niveaux_dict = dict(
            self.NIVEAUX_BTS + 
            self.NIVEAUX_LICENCE + 
            self.NIVEAUX_MASTER + 
            self.NIVEAUX_INGENIEUR
        )
        return niveaux_dict.get(self.niveau, self.niveau)
    @property
    def full_name(self):
        return f"{self.prenom} {self.nom}"

# Modèle simple pour gérer l'état global de l'élection
class ElectionState(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('active', 'Active'),
        ('closed', 'Terminée'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # Assurer qu'il n'y a qu'une seule instance de ce modèle
    def save(self, *args, **kwargs):
        self.pk = 1
        if self.status == 'pending':
            candidates = Candidate.objects.all()
            for candidate in candidates:
                candidate.votes = 0
                candidate.save()
            
            Vote.objects.all().delete() # eface tous les votes
            # Réinitialiser le statut "a voté" pour tous les utilisateurs
            Profile.objects.all().update(has_voted=False)

        super(ElectionState, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass # Empêcher la suppression

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"État de l'élection : {self.get_status_display()}"

class Vote(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='vote_records')
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['profile',]
        ordering = ['-voted_at']
    
    def delete(self, *args, **kwargs):
        self.profile.has_voted = False
        self.profile.save()
        self.candidate.votes -= 1
        self.candidate.save()

        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"{self.profile.matricule} a voté pour {self.candidate.name}"