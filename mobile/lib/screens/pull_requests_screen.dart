import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/pull_request.dart';
import '../providers/project_status_provider.dart';

class PullRequestsScreen extends ConsumerStatefulWidget {
  final int projectId;
  final String projectName;

  const PullRequestsScreen({super.key, required this.projectId, required this.projectName});

  @override
  ConsumerState<PullRequestsScreen> createState() => _PullRequestsScreenState();
}

class _PullRequestsScreenState extends ConsumerState<PullRequestsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String? _selectedStatus;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _tabController.addListener(() {
      setState(() {
        switch (_tabController.index) {
          case 0:
            _selectedStatus = null; // All
            break;
          case 1:
            _selectedStatus = 'pending';
            break;
          case 2:
            _selectedStatus = 'approved';
            break;
          case 3:
            _selectedStatus = 'merged';
            break;
        }
      });
      _refreshPullRequests();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _refreshPullRequests() {
    ref.read(pullRequestsProvider(widget.projectId).notifier)
        .fetchPullRequestsWithFilters(status: _selectedStatus);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.projectName} - Pull Requests'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'All'),
            Tab(text: 'Pending'),
            Tab(text: 'Approved'),
            Tab(text: 'Merged'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refreshPullRequests,
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildPullRequestList(null), // All
          _buildPullRequestList('pending'), // Pending
          _buildPullRequestList('approved'), // Approved
          _buildPullRequestList('merged'), // Merged
        ],
      ),
    );
  }

  Widget _buildPullRequestList(String? status) {
    final pullRequestsAsync = ref.watch(pullRequestsProvider(widget.projectId));

    return pullRequestsAsync.when(
      data: (pullRequests) {
        final filteredPullRequests = status == null 
            ? pullRequests 
            : pullRequests.where((pr) => pr.status == status).toList();

        if (filteredPullRequests.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  status == null ? Icons.merge_type : _getStatusIcon(status),
                  size: 64,
                  color: Colors.grey,
                ),
                const SizedBox(height: 16),
                Text(
                  status == null ? 'No pull requests found' : 'No $status pull requests',
                  style: const TextStyle(fontSize: 18, color: Colors.grey),
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.all(8),
          itemCount: filteredPullRequests.length,
          itemBuilder: (context, index) {
            final pr = filteredPullRequests[index];
            return _buildPullRequestCard(pr);
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, stack) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text('Error: $error'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _refreshPullRequests,
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPullRequestCard(PullRequest pr) {
    Color statusColor = _getStatusColor(pr.status);
    IconData statusIcon = _getStatusIcon(pr.status);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      elevation: 2,
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: statusColor.withOpacity(0.2),
          child: Icon(statusIcon, color: statusColor),
        ),
        title: Text(
          pr.title,
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(Icons.person, size: 16, color: Colors.grey[600]),
                const SizedBox(width: 4),
                Text(pr.requester, style: TextStyle(color: Colors.grey[600])),
                const SizedBox(width: 16),
                Icon(Icons.schedule, size: 16, color: Colors.grey[600]),
                const SizedBox(width: 4),
                Text(pr.formattedDateTime, style: TextStyle(color: Colors.grey[600])),
              ],
            ),
            if (pr.sourceBranch != null && pr.targetBranch != null) ...[
              const SizedBox(height: 4),
              Row(
                children: [
                  Icon(Icons.compare_arrows, size: 16, color: Colors.grey[600]),
                  const SizedBox(width: 4),
                  Text(
                    '${pr.sourceBranch} → ${pr.targetBranch}',
                    style: TextStyle(color: Colors.grey[600]),
                  ),
                ],
              ),
            ],
          ],
        ),
        trailing: Chip(
          label: Text(
            pr.status.toUpperCase(),
            style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
          ),
          backgroundColor: statusColor.withOpacity(0.2),
          side: BorderSide(color: statusColor),
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (pr.description.isNotEmpty) ...[
                  const Text(
                    'Description:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(pr.description),
                  const SizedBox(height: 12),
                ],
                Row(
                  children: [
                    Text('PR ID: #${pr.id}'),
                    const Spacer(),
                    if (pr.repositoryUrl != null)
                      TextButton.icon(
                        onPressed: () {
                          // TODO: Open repository URL
                        },
                        icon: const Icon(Icons.link, size: 16),
                        label: const Text('View in Repo'),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'pending':
        return Colors.orange;
      case 'approved':
        return Colors.lightGreen;
      case 'merged':
        return Colors.green;
      case 'rejected':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  IconData _getStatusIcon(String status) {
    switch (status) {
      case 'pending':
        return Icons.hourglass_empty;
      case 'approved':
        return Icons.check_circle_outline;
      case 'merged':
        return Icons.merge_type;
      case 'rejected':
        return Icons.cancel;
      default:
        return Icons.help_outline;
    }
  }
}
