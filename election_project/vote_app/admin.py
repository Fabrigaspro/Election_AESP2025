from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Profile, Candidate, ElectionState, Vote

# Personnalisation basique de l'interface
admin.site.site_header = "Administration AESP - Système de Vote"
admin.site.site_title = "AESP Voting Admin"
admin.site.index_title = "Tableau de bord"

@admin.register(Profile)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('matricule','get_fullname','role', 'status', 'cycle', 'specialite', 'niveau', 'is_connected', 'has_voted', 'is_admin', 'photo', 'recu')
    list_filter = ('role', 'status', 'cycle', 'niveau')
    search_fields = ('cycle', 'niveau',)

    def get_fullname(self, obj):
        return obj.get_fullname()
    

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'cycle', 'specialite', 'niveau', 'votes', 'photo_url' )
    search_fields = ('nom', 'specialite')

@admin.register(ElectionState)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('status',)
    list_filter = ('status',)
    search_fields = ('title',)

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('profile', 'candidate', 'voted_at')
    list_filter = ('voted_at',)
    readonly_fields = ('voted_at',)