import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../providers/dashboard_provider.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget { // Changed to ConsumerStatefulWidget
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState(); // Changed to ConsumerState
}

class _LoginScreenState extends ConsumerState<LoginScreen> { // Changed to ConsumerState<LoginScreen>
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  bool _obscurePassword = true;
  String? _error;
  int _logoTapCount = 0;
  DateTime? _lastLogoTap;

  Future<void> _handleLogin() async { // Removed WidgetRef ref parameter
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final clientAsyncValue = ref.read(apiClientProvider);
      if (clientAsyncValue.value == null) {
        throw Exception('API Client not initialized');
      }
      final client = clientAsyncValue.value!;
      
      final response = await client.dio.post('/auth/login/', data: {
        'username': _usernameController.text,
        'password': _passwordController.text,
      });

      final token = response.data['token'];
      await ref.read(authStateProvider.notifier).login(token, _usernameController.text);
      
      // Removed manual Navigator.pushReplacement as main.dart handles it
    } on DioException catch (e) {
      setState(() {
        if (e.type == DioExceptionType.connectionTimeout || 
            e.type == DioExceptionType.receiveTimeout) {
          _error = 'Connection timed out. Check your server IP.';
        } else if (e.type == DioExceptionType.connectionError) {
          _error = 'Connection refused. Is the server running?';
        } else if (e.response?.statusCode == 401) {
          _error = 'Invalid username or password.';
        } else if (e.response?.statusCode == 404) {
          _error = 'Login endpoint not found (404).';
        } else {
          _error = 'Error: ${e.message}';
        }
      });
    } catch (e) {
      setState(() {
        _error = 'Login failed: ${e.toString()}';
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _handleLogoTap() {
    final now = DateTime.now();
    if (_lastLogoTap == null || now.difference(_lastLogoTap!) > const Duration(seconds: 2)) {
      _logoTapCount = 1;
    } else {
      _logoTapCount++;
    }
    _lastLogoTap = now;

    if (_logoTapCount == 4) {
      _logoTapCount = 0;
      _showEditUrlDialog();
    }
  }

  void _showEditUrlDialog() {
    final client = ref.read(apiClientProvider).value;
    if (client == null) return;

    final controller = TextEditingController(text: client.baseUrl);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit API Base URL'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: 'http://192.168.1.1:8000/api'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              ref.read(apiClientProvider.notifier).setBaseUrl(controller.text);
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('API URL updated')),
              );
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F0F23),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              GestureDetector(
                onTap: _handleLogoTap,
                child: Image.asset(
                  'assets/logo.png',
                  width: MediaQuery.of(context).size.width * 0.9,
                  fit: BoxFit.contain,
                  errorBuilder: (context, error, stackTrace) => const Icon(
                    Icons.security,
                    size: 80,
                    color: Color(0xFF3B82F6),
                  ),
                ),
              ),
              const SizedBox(height: 48),
              TextField(
                controller: _usernameController,
                style: const TextStyle(color: Colors.white),
                decoration: _inputDecoration('Username', Icons.person),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passwordController,
                obscureText: _obscurePassword,
                style: const TextStyle(color: Colors.white),
                decoration: _inputDecoration('Password', Icons.lock).copyWith(
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword ? Icons.visibility_off : Icons.visibility,
                      color: Colors.white38,
                    ),
                    onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                  ),
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 16),
                Text(_error!, style: const TextStyle(color: Colors.redAccent, fontSize: 12)),
              ],
              const SizedBox(height: 32),
              // Consumer widget is no longer needed here as ref is directly available in ConsumerState
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : () => _handleLogin(), // Removed ref argument
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF3B82F6),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: _isLoading 
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('Login', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String label, IconData icon) {
    return InputDecoration(
      labelText: label,
      labelStyle: const TextStyle(color: Colors.white38),
      prefixIcon: Icon(icon, color: Colors.white38),
      filled: true,
      fillColor: const Color(0xFF181929),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF3B82F6))),
    );
  }
}
