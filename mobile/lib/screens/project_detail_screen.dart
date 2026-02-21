import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/project.dart';
import '../providers/project_provider.dart'; // For refreshing projects if needed
import '../core/api_client.dart'; // For API calls
import '../providers/dashboard_provider.dart'; // Import for apiClientProvider

class ProjectDetailScreen extends ConsumerStatefulWidget {
  final Project project;

  const ProjectDetailScreen({super.key, required this.project});

  @override
  ConsumerState<ProjectDetailScreen> createState() => _ProjectDetailScreenState();
}

class _ProjectDetailScreenState extends ConsumerState<ProjectDetailScreen> {
  final List<Server> _selectedServers = [];
  bool _isLoading = false;
  String _commandOutput = '';

  @override
  void initState() {
    super.initState();
    _commandOutput = ''; // Clear output on init
  }

  void _runGitPull() async {
    if (_selectedServers.isEmpty) {
      _showSnackBar('Please select at least one server.');
      return;
    }

    setState(() {
      _isLoading = true;
      _commandOutput = '''Initiating Git pull...\n''';
    });

    try {
      final apiClient = ref.read(apiClientProvider).value!; // Use .value! for sync access after future is resolved by Riverpod
      final serverIds = _selectedServers.map((s) => s.id).toList();
      final response = await apiClient.dio.post(
        '/projects/${widget.project.id}/git-pull/',
        data: {'server_ids': serverIds},
      );

      _commandOutput = ''; // Clear previous output
      if (response.statusCode == 200) {
        for (var result in response.data) {
          _commandOutput += '''Server: ${result['hostname']} (ID: ${result['server_id']})
Status: ${result['success'] ? 'SUCCESS' : 'FAILED'}
''';
          if (result['stdout'].isNotEmpty) {
            _commandOutput += '''STDOUT:
${result['stdout']}
''';
          }
          if (result['stderr'].isNotEmpty) {
            _commandOutput += '''STDERR:
${result['stderr']}
''';
          }
          _commandOutput += '''Exit Code: ${result['exit_code']}\n\n''';
        }
      } else {
        _commandOutput = '''Error: ${response.statusCode} - ${response.data}\n''';
      }
    } catch (e) {
      _commandOutput = '''Error running Git pull: $e\n''';
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _runCustomCommand() async {
    if (_selectedServers.isEmpty) {
      _showSnackBar('Please select at least one server.');
      return;
    }

    // Show a dialog to get the command from the user
    final command = await showDialog<String>(
      context: context,
      builder: (BuildContext dialogContext) {
        TextEditingController commandController = TextEditingController();
        return AlertDialog(
          title: const Text('Run Custom Command'),
          content: TextField(
            controller: commandController,
            decoration: const InputDecoration(hintText: 'Enter command'),
          ),
          actions: <Widget>[
            TextButton(
              child: const Text('Cancel'),
              onPressed: () {
                Navigator.of(dialogContext).pop();
              },
            ),
            TextButton(
              child: const Text('Run'),
              onPressed: () {
                Navigator.of(dialogContext).pop(commandController.text);
              },
            ),
          ],
        );
      },
    );

    if (command == null || command.trim().isEmpty) {
      _showSnackBar('No command entered.');
      return;
    }

    setState(() {
      _isLoading = true;
      _commandOutput = '''Executing custom command: "$command"...\n''';
    });

    try {
      final apiClient = ref.read(apiClientProvider).value!; // Use .value! for sync access after future is resolved by Riverpod
      final serverIds = _selectedServers.map((s) => s.id).toList();
      final response = await apiClient.dio.post(
        '/projects/${widget.project.id}/run-command/',
        data: {'server_ids': serverIds, 'command': command},
      );

      _commandOutput = ''; // Clear previous output
      if (response.statusCode == 200) {
        for (var result in response.data) {
          _commandOutput += '''Server: ${result['hostname']} (ID: ${result['server_id']})
Status: ${result['success'] ? 'SUCCESS' : 'FAILED'}
''';
          if (result['stdout'].isNotEmpty) {
            _commandOutput += '''STDOUT:
${result['stdout']}
''';
          }
          if (result['stderr'].isNotEmpty) {
            _commandOutput += '''STDERR:
${result['stderr']}
''';
          }
          _commandOutput += '''Exit Code: ${result['exit_code']}\n\n''';
        }
      } else {
        _commandOutput = '''Error: ${response.statusCode} - ${response.data}\n''';
      }
    } catch (e) {
      _commandOutput = '''Error running custom command: $e\n''';
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.project.name),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Repo URL: ${widget.project.repoUrl}', style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 20),
            Text('Servers (${widget.project.servers.length}):', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            ...widget.project.servers.map((server) {
              return CheckboxListTile(
                title: Text('${server.hostname} (${server.user}:${server.path})'),
                value: _selectedServers.contains(server),
                onChanged: _isLoading ? null : (bool? selected) {
                  setState(() {
                    if (selected == true) {
                      _selectedServers.add(server);
                    } else {
                      _selectedServers.remove(server);
                    }
                  });
                },
              );
            }).toList(),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isLoading ? null : _runGitPull,
                    icon: _isLoading && _commandOutput.startsWith('Initiating Git pull') ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.cloud_download),
                    label: const Text('Run Git Pull'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isLoading ? null : _runCustomCommand,
                    icon: _isLoading && _commandOutput.startsWith('Executing custom command') ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.terminal),
                    label: const Text('Run Command'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (_isLoading || _commandOutput.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(12),
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.grey[800],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: SingleChildScrollView(
                  child: Text(
                    _commandOutput,
                    style: const TextStyle(color: Colors.white, fontFamily: 'monospace'),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
