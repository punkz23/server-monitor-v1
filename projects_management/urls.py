from django.urls import path
from .views import ProjectListView, ProjectDetailView, GitPullView, CustomCommandView

urlpatterns = [
    path('projects/', ProjectListView.as_view(), name='project-list'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('projects/<int:pk>/git-pull/', GitPullView.as_view(), name='project-git-pull'),
    path('projects/<int:pk>/run-command/', CustomCommandView.as_view(), name='project-run-command'),
]
