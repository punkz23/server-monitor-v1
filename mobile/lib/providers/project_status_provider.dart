import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/pull_request.dart';
import 'dashboard_provider.dart'; // Import for apiClientProvider

// Provider for project status
final projectStatusProvider = AsyncNotifierProvider.family<ProjectStatusNotifier, ProjectStatus?, int>(
  ProjectStatusNotifier.new,
);

// Provider for today's pull requests
final todayPullRequestsProvider = AsyncNotifierProvider.family<TodayPullRequestsNotifier, List<PullRequest>, int>(
  TodayPullRequestsNotifier.new,
);

// Provider for all pull requests
final pullRequestsProvider = AsyncNotifierProvider.family<PullRequestsNotifier, List<PullRequest>, int>(
  PullRequestsNotifier.new,
);

class ProjectStatusNotifier extends FamilyAsyncNotifier<ProjectStatus?, int> {
  @override
  Future<ProjectStatus?> build(int projectId) async {
    try {
      final apiClient = await ref.watch(apiClientProvider.future);
      return await apiClient.fetchProjectStatus(projectId);
    } catch (e) {
      // Return null if status fetch fails, allowing UI to handle gracefully
      return null;
    }
  }

  // Method to refresh project status
  Future<void> refreshStatus() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => build(arg));
  }
}

class TodayPullRequestsNotifier extends FamilyAsyncNotifier<List<PullRequest>, int> {
  @override
  Future<List<PullRequest>> build(int projectId) async {
    try {
      final apiClient = await ref.watch(apiClientProvider.future);
      return await apiClient.fetchTodayPullRequests(projectId);
    } catch (e) {
      // Return empty list if fetch fails
      return [];
    }
  }

  // Method to refresh today's pull requests
  Future<void> refreshTodayPullRequests() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => build(arg));
  }
}

class PullRequestsNotifier extends FamilyAsyncNotifier<List<PullRequest>, int> {
  String? _currentStatus;
  DateTime? _currentDate;

  @override
  Future<List<PullRequest>> build(int projectId) async {
    try {
      final apiClient = await ref.watch(apiClientProvider.future);
      return await apiClient.fetchPullRequests(projectId, status: _currentStatus, date: _currentDate);
    } catch (e) {
      // Return empty list if fetch fails
      return [];
    }
  }

  // Method to fetch pull requests with filters
  Future<void> fetchPullRequestsWithFilters({String? status, DateTime? date}) async {
    _currentStatus = status;
    _currentDate = date;
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => build(arg));
  }

  // Method to refresh pull requests
  Future<void> refreshPullRequests() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => build(arg));
  }
}
