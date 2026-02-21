import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/dashboard_provider.dart'; // Contains apiClientProvider

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _baseUrlController = TextEditingController();
  String? _currentBaseUrl;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadCurrentBaseUrl();
  }

  Future<void> _loadCurrentBaseUrl() async {
    final apiClient = await ref.read(apiClientProvider.future);
    setState(() {
      _currentBaseUrl = apiClient.baseUrl;
      _baseUrlController.text = _currentBaseUrl!;
      _isLoading = false;
    });
  }

  Future<void> _saveBaseUrl() async {
    if (_baseUrlController.text.isNotEmpty && _baseUrlController.text != _currentBaseUrl) {
      await ref.read(apiClientProvider.notifier).setBaseUrl(_baseUrlController.text);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('API URL updated successfully!')),
      );
      setState(() {
        _currentBaseUrl = _baseUrlController.text;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Settings')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        backgroundColor: Theme.of(context).colorScheme.surface,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Configure API Base URL',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _baseUrlController,
              decoration: InputDecoration(
                labelText: 'API Base URL',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                hintText: 'e.g., http://192.168.1.100:8000/api',
              ),
              keyboardType: TextInputType.url,
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _saveBaseUrl,
                icon: const Icon(Icons.save),
                label: const Text('Save API URL'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Current URL: $_currentBaseUrl',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}
