import 'package:flutter/material.dart';
import 'dashboard_screen.dart';
import 'server_list_screen.dart';
import 'alert_history_screen.dart';
import 'ssl_manager_screen.dart';
import 'projects_screen.dart'; // Import the ProjectsScreen

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _selectedIndex = 0;

  final List<Widget> _screens = [
    const DashboardScreen(),
    const ServerListScreen(),
    const AlertHistoryScreen(),
    const SslManagerScreen(),
    const ProjectsScreen(), // Add ProjectsScreen to the list of screens
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        type: BottomNavigationBarType.fixed,
        backgroundColor: const Color(0xFF181929),
        selectedItemColor: const Color(0xFF3B82F6),
        unselectedItemColor: Colors.white24,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard_outlined), activeIcon: Icon(Icons.dashboard), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.dns_outlined), activeIcon: Icon(Icons.dns), label: 'Servers'),
          BottomNavigationBarItem(icon: Icon(Icons.notifications_outlined), activeIcon: Icon(Icons.notifications), label: 'Alerts'),
          BottomNavigationBarItem(icon: Icon(Icons.verified_user_outlined), activeIcon: Icon(Icons.verified_user), label: 'SSL'),
          BottomNavigationBarItem(icon: Icon(Icons.folder_open_outlined), activeIcon: Icon(Icons.folder), label: 'Projects'), // Add new item for Projects
        ],
      ),
    );
  }
}
