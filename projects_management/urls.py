from django.urls import path
from .views import (
    ProjectListView, ProjectDetailView, GitPullView, 
    CustomCommandView, ProjectStatusView, PullRequestListView, 
    TodayPullRequestListView
)

urlpatterns = [
    path('projects/', ProjectListView.as_view(), name='project-list'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('projects/<int:pk>/status/', ProjectStatusView.as_view(), name='project-status'),
    path('projects/<int:pk>/pull-requests/', PullRequestListView.as_view(), name='project-pull-requests'),
    path('projects/<int:pk>/pull-requests/today/', TodayPullRequestListView.as_view(), name='project-pull-requests-today'),
    path('projects/<int:pk>/git-pull/', GitPullView.as_view(), name='project-git-pull'),
    path('projects/<int:pk>/run-command/', CustomCommandView.as_view(), name='project-run-command'),
]
