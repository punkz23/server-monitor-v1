import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dashboard_provider.dart';

final authStateProvider = StateNotifierProvider<AuthNotifier, bool>((ref) {
  return AuthNotifier(ref);
});

class AuthNotifier extends StateNotifier<bool> {
  final Ref _ref;
  Timer? _inactivityTimer;
  static const _inactivityDuration = Duration(minutes: 5);

  AuthNotifier(this._ref) : super(false) {
    _checkInitialAuth();
  }

  Future<void> _checkInitialAuth() async {
    final client = _ref.read(apiClientProvider).value;
    if (client != null) {
      final hasToken = await client.hasToken();
      state = hasToken;
      if (hasToken) {
        _startTimer();
      }
    }
  }

  void _startTimer() {
    _inactivityTimer?.cancel();
    _inactivityTimer = Timer(_inactivityDuration, () {
      logout();
    });
  }

  void resetTimer() {
    if (state) {
      _startTimer();
    }
  }

  Future<void> login(String token, String username) async {
    final client = _ref.read(apiClientProvider).value;
    if (client != null) {
      await client.saveToken(token);
      await client.saveUser(username);
      state = true;
      _startTimer();
    }
  }

  Future<void> logout() async {
    final client = _ref.read(apiClientProvider).value;
    if (client != null) {
      await client.deleteToken();
      _inactivityTimer?.cancel();
      state = false;
    }
  }

  @override
  void dispose() {
    _inactivityTimer?.cancel();
    super.dispose();
  }
}

final usernameProvider = FutureProvider<String?>((ref) async {
  final client = ref.watch(apiClientProvider).value;
  if (client != null) {
    return await client.getUser();
  }
  return null;
});
