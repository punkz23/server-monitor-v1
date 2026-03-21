import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/project_provider.dart';
import '../providers/project_status_provider.dart';
import 'project_detail_screen.dart'; // Import ProjectDetailScreen

class ProjectsScreen extends ConsumerWidget {
  const ProjectsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projectsAsyncValue = ref.watch(projectsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Project Management'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(projectsProvider); // Refresh projects
            },
          ),
        ],
      ),
      body: projectsAsyncValue.when(
        data: (projects) {
          if (projects.isEmpty) {
            return const Center(child: Text('No projects found.'));
          }
          return ListView.builder(
            itemCount: projects.length,
            itemBuilder: (context, index) {
              final project = projects[index];
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                child: Consumer(
                  builder: (context, ref, child) {
                    final todayPrsAsync = ref.watch(todayPullRequestsProvider(project.id));
                    
                    return ListTile(
                      title: Text(project.name),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(project.repoUrl),
                          const SizedBox(height: 4),
                          todayPrsAsync.when(
                            data: (todayPrs) {
                              if (todayPrs.isEmpty) {
                                return const Text('No PRs today', style: TextStyle(fontSize: 12, color: Colors.grey));
                              }
                              final pendingCount = todayPrs.where((pr) => pr.status == 'pending').length;
                              final doneCount = todayPrs.where((pr) => pr.status == 'merged' || pr.status == 'approved').length;
                              return Row(
                                children: [
                                  Text(
                                    'Today: ${todayPrs.length} PRs',
                                    style: const TextStyle(fontSize: 12, color: Colors.blue),
                                  ),
                                  const SizedBox(width: 8),
                                  if (pendingCount > 0)
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: Colors.orange.withOpacity(0.2),
                                        borderRadius: BorderRadius.circular(10),
                                        border: Border.all(color: Colors.orange),
                                      ),
                                      child: Text(
                                        '$pendingCount pending',
                                        style: const TextStyle(fontSize: 10, color: Colors.orange),
                                      ),
                                    ),
                                  if (doneCount > 0) ...[
                                    const SizedBox(width: 4),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: Colors.green.withOpacity(0.2),
                                        borderRadius: BorderRadius.circular(10),
                                        border: Border.all(color: Colors.green),
                                      ),
                                      child: Text(
                                        '$doneCount done',
                                        style: const TextStyle(fontSize: 10, color: Colors.green),
                                      ),
                                    ),
                                  ],
                                ],
                              );
                            },
                            loading: () => const SizedBox(
                              width: 12,
                              height: 12,
                              child: CircularProgressIndicator(strokeWidth: 1),
                            ),
                            error: (_, __) => const Text(
                              'Status unavailable',
                              style: TextStyle(fontSize: 12, color: Colors.red),
                            ),
                          ),
                        ],
                      ),
                      trailing: const Icon(Icons.arrow_forward_ios),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => ProjectDetailScreen(project: project),
                          ),
                        );
                      },
                    );
                  },
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }
}
