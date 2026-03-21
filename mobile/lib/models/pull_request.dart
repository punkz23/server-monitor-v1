class PullRequest {
  final int id;
  final String title;
  final String description;
  final String requester;
  final String status; // 'pending', 'approved', 'merged', 'rejected'
  final DateTime createdAt;
  final DateTime? updatedAt;
  final String? sourceBranch;
  final String? targetBranch;
  final String? repositoryUrl;

  PullRequest({
    required this.id,
    required this.title,
    required this.description,
    required this.requester,
    required this.status,
    required this.createdAt,
    this.updatedAt,
    this.sourceBranch,
    this.targetBranch,
    this.repositoryUrl,
  });

  factory PullRequest.fromJson(Map<String, dynamic> json) {
    return PullRequest(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      requester: json['requester'] ?? json['author'] ?? 'Unknown',
      status: json['status'] ?? 'pending',
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
      updatedAt: json['updated_at'] != null ? DateTime.parse(json['updated_at']) : null,
      sourceBranch: json['source_branch'],
      targetBranch: json['target_branch'],
      repositoryUrl: json['repository_url'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'requester': requester,
      'status': status,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
      'source_branch': sourceBranch,
      'target_branch': targetBranch,
      'repository_url': repositoryUrl,
    };
  }

  // Helper method to check if PR was created today
  bool isCreatedToday() {
    final now = DateTime.now();
    return createdAt.year == now.year &&
           createdAt.month == now.month &&
           createdAt.day == now.day;
  }

  // Helper method to format date time for display
  String get formattedDateTime {
    return '${createdAt.day.toString().padLeft(2, '0')}/'
           '${createdAt.month.toString().padLeft(2, '0')}/'
           '${createdAt.year} '
           '${createdAt.hour.toString().padLeft(2, '0')}:'
           '${createdAt.minute.toString().padLeft(2, '0')}';
  }
}

class ProjectStatus {
  final int projectId;
  final int totalPullRequests;
  final int pendingPullRequests;
  final int approvedPullRequests;
  final int mergedPullRequests;
  final int rejectedPullRequests;
  final List<PullRequest> todayPullRequests;
  final DateTime lastUpdated;

  ProjectStatus({
    required this.projectId,
    required this.totalPullRequests,
    required this.pendingPullRequests,
    required this.approvedPullRequests,
    required this.mergedPullRequests,
    required this.rejectedPullRequests,
    required this.todayPullRequests,
    required this.lastUpdated,
  });

  factory ProjectStatus.fromJson(Map<String, dynamic> json) {
    var todayPrsList = json['today_pull_requests'] as List? ?? [];
    List<PullRequest> todayPrs = todayPrsList.map((pr) => PullRequest.fromJson(pr)).toList();

    return ProjectStatus(
      projectId: json['project_id'] ?? 0,
      totalPullRequests: json['total_pull_requests'] ?? 0,
      pendingPullRequests: json['pending_pull_requests'] ?? 0,
      approvedPullRequests: json['approved_pull_requests'] ?? 0,
      mergedPullRequests: json['merged_pull_requests'] ?? 0,
      rejectedPullRequests: json['rejected_pull_requests'] ?? 0,
      todayPullRequests: todayPrs,
      lastUpdated: DateTime.parse(json['last_updated'] ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'project_id': projectId,
      'total_pull_requests': totalPullRequests,
      'pending_pull_requests': pendingPullRequests,
      'approved_pull_requests': approvedPullRequests,
      'merged_pull_requests': mergedPullRequests,
      'rejected_pull_requests': rejectedPullRequests,
      'today_pull_requests': todayPullRequests.map((pr) => pr.toJson()).toList(),
      'last_updated': lastUpdated.toIso8601String(),
    };
  }

  // Helper method to get today's PR counts
  int get todayPendingCount => todayPullRequests.where((pr) => pr.status == 'pending').length;
  int get todayApprovedCount => todayPullRequests.where((pr) => pr.status == 'approved').length;
  int get todayMergedCount => todayPullRequests.where((pr) => pr.status == 'merged').length;
  int get todayRejectedCount => todayPullRequests.where((pr) => pr.status == 'rejected').length;
  int get todayTotalCount => todayPullRequests.length;
}
