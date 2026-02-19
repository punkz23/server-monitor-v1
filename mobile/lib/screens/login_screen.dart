import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../providers/dashboard_provider.dart';
import 'main_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  Future<void> _handleLogin(WidgetRef ref) async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final client = ref.read(apiClientProvider);
      final response = await client.dio.post('/auth/login/', data: {
        'username': _usernameController.text,
        'password': _passwordController.text,
      });

      final token = response.data['token'];
      await client.saveToken(token);

      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const MainScreen()),
        );
      }
    } catch (e) {
      setState(() {
        _error = 'Login failed. Please check your credentials.';
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
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
              const Icon(Icons.security, size: 80, color: Color(0xFF3B82F6)),
              const SizedBox(height: 24),
              const Text(
                'ServerWatch Mobile',
                style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
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
                obscureText: true,
                style: const TextStyle(color: Colors.white),
                decoration: _inputDecoration('Password', Icons.lock),
              ),
              if (_error != null) ...[
                const SizedBox(height: 16),
                Text(_error!, style: const TextStyle(color: Colors.redAccent, fontSize: 12)),
              ],
              const SizedBox(height: 32),
              Consumer(builder: (context, ref, _) {
                return SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : () => _handleLogin(ref),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF3B82F6),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: _isLoading 
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('Login', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  ),
                );
              }),
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
