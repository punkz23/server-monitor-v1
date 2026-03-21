import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/pull_request.dart';
import '../providers/project_status_provider.dart';

class ProjectStatusWidget extends ConsumerWidget {
  final int projectId;

  const ProjectStatusWidget({super.key, required this.projectId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projectStatusAsync = ref.watch(projectStatusProvider(projectId));
    final todayPullRequestsAsync = ref.watch(todayPullRequestsProvider(projectId));

    return Card(
      margin: const EdgeInsets.all(8.0),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Project Status',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            
            // Overall Status
            projectStatusAsync.when(
              data: (status) {
                if (status == null) {
                  return const Text('Status information unavailable');
                }
                return _buildOverallStatus(status);
              },
              loading: () => const CircularProgressIndicator(),
              error: (error, stack) => Text('Error: $error'),
            ),
            
            const SizedBox(height: 16),
            
            // Today's Pull Requests
            const Text(
              "Today's Pull Requests",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            
            todayPullRequestsAsync.when(
              data: (pullRequests) {
                if (pullRequests.isEmpty) {
                  return const Text('No pull requests today');
                }
                return _buildTodayPullRequests(pullRequests);
              },
              loading: () => const CircularProgressIndicator(),
              error: (error, stack) => Text('Error: $error'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOverallStatus(ProjectStatus status) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            _buildStatusChip('Total', status.totalPullRequests, Colors.blue),
            const SizedBox(width: 8),
            _buildStatusChip('Pending', status.pendingPullRequests, Colors.orange),
            const SizedBox(width: 8),
            _buildStatusChip('Merged', status.mergedPullRequests, Colors.green),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            _buildStatusChip('Approved', status.approvedPullRequests, Colors.lightGreen),
            const SizedBox(width: 8),
            _buildStatusChip('Rejected', status.rejectedPullRequests, Colors.red),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          'Last updated: ${_formatDateTime(status.lastUpdated)}',
          style: const TextStyle(fontSize: 12, color: Colors.grey),
        ),
      ],
    );
  }

  Widget _buildStatusChip(String label, int count, Color color) {
    return Chip(
      label: Text('$label: $count'),
      backgroundColor: color.withOpacity(0.2),
      side: BorderSide(color: color),
    );
  }

  Widget _buildTodayPullRequests(List<PullRequest> pullRequests) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Summary for today
        Row(
          children: [
            _buildStatusChip('Today Total', pullRequests.length, Colors.blue),
            const SizedBox(width: 8),
            _buildStatusChip('Pending', pullRequests.where((pr) => pr.status == 'pending').length, Colors.orange),
            const SizedBox(width: 8),
            _buildStatusChip('Done', pullRequests.where((pr) => pr.status == 'merged' || pr.status == 'approved').length, Colors.green),
          ],
        ),
        
        const SizedBox(height: 12),
        
        // List of today's pull requests
        ...pullRequests.map((pr) => _buildPullRequestTile(pr)).toList(),
      ],
    );
  }

  Widget _buildPullRequestTile(PullRequest pr) {
    Color statusColor;
    switch (pr.status) {
      case 'pending':
        statusColor = Colors.orange;
        break;
      case 'approved':
        statusColor = Colors.lightGreen;
        break;
      case 'merged':
        statusColor = Colors.green;
        break;
      case 'rejected':
        statusColor = Colors.red;
        break;
      default:
        statusColor = Colors.grey;
    }

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4.0),
      child: ListTile(
        dense: true,
        leading: CircleAvatar(
          backgroundColor: statusColor.withOpacity(0.2),
          child: Icon(
            Icons.merge_type,
            color: statusColor,
            size: 20,
          ),
        ),
        title: Text(
          pr.title,
          style: const TextStyle(fontWeight: FontWeight.w500),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Requester: ${pr.requester}'),
            Text('Time: ${pr.formattedDateTime}'),
            if (pr.sourceBranch != null && pr.targetBranch != null)
              Text('${pr.sourceBranch} → ${pr.targetBranch}'),
          ],
        ),
        trailing: Chip(
          label: Text(
            pr.status.toUpperCase(),
            style: const TextStyle(fontSize: 10),
          ),
          backgroundColor: statusColor.withOpacity(0.2),
          side: BorderSide(color: statusColor),
        ),
      ),
    );
  }

  String _formatDateTime(DateTime dateTime) {
    return '${dateTime.day.toString().padLeft(2, '0')}/'
           '${dateTime.month.toString().padLeft(2, '0')}/'
           '${dateTime.year} '
           '${dateTime.hour.toString().padLeft(2, '0')}:'
           '${dateTime.minute.toString().padLeft(2, '0')}';
  }
}
