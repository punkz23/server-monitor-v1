import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/project.dart';
import 'dashboard_provider.dart'; // Assuming apiClientProvider is here

final projectsProvider = AsyncNotifierProvider<ProjectsNotifier, List<Project>>(() {
  return ProjectsNotifier();
});

class ProjectsNotifier extends AsyncNotifier<List<Project>> {
  @override
  Future<List<Project>> build() async {
    final apiClient = await ref.watch(apiClientProvider.future);
    return apiClient.fetchProjects();
  }

  // Method to refresh projects
  Future<void> refreshProjects() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => build());
  }
}
