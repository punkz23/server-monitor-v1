import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/login_screen.dart';
import 'screens/main_screen.dart';
import 'core/api_client.dart';
import 'providers/dashboard_provider.dart';
import 'providers/auth_provider.dart';

void main() {
  runApp(const ProviderScope(child: ServerWatchApp()));
}

class ServerWatchApp extends ConsumerWidget {
  const ServerWatchApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isLoggedIn = ref.watch(authStateProvider);

    return Listener(
      onPointerDown: (_) => ref.read(authStateProvider.notifier).resetTimer(),
      onPointerMove: (_) => ref.read(authStateProvider.notifier).resetTimer(),
      onPointerUp: (_) => ref.read(authStateProvider.notifier).resetTimer(),
      child: MaterialApp(
        key: ValueKey('app_isLoggedIn_$isLoggedIn'),
        title: 'ServerWatch',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          brightness: Brightness.dark,
          primaryColor: const Color(0xFF3B82F6),
          scaffoldBackgroundColor: const Color(0xFF0F0F23),
          textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
          colorScheme: const ColorScheme.dark(
            primary: Color(0xFF3B82F6),
            secondary: Color(0xFF8B5CF6),
            surface: Color(0xFF181929),
          ),
          useMaterial3: true,
        ),
        home: ref.watch(apiClientProvider).when(
          data: (apiClient) {
            return isLoggedIn ? const MainScreen() : const LoginScreen();
          },
          loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
          error: (err, stack) => Scaffold(body: Center(child: Text('Error: $err'))),
        ),
      ),
    );
  }
}
