import 'package:flutter/material.dart';
import 'dashboard_screen.dart';
import 'server_list_screen.dart';
import 'alert_history_screen.dart';
import 'ssl_manager_screen.dart';
import 'projects_screen.dart';
import 'network_devices_screen.dart';
import 'dtr_monitoring_screen.dart';

// ── Nav item definition ───────────────────────────────────────────────────────
class _NavItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  const _NavItem(this.icon, this.activeIcon, this.label);
}

const _navItems = [
  _NavItem(Icons.dashboard_outlined,     Icons.dashboard,      'Dashboard'),
  _NavItem(Icons.dns_outlined,           Icons.dns,            'Servers'),
  _NavItem(Icons.router_outlined,        Icons.router,         'Network'),
  _NavItem(Icons.notifications_outlined, Icons.notifications,  'Alerts'),
  _NavItem(Icons.verified_user_outlined, Icons.verified_user,  'SSL'),
  _NavItem(Icons.folder_open_outlined,   Icons.folder,         'Projects'),
  _NavItem(Icons.fingerprint_outlined,   Icons.fingerprint,    'DTR'),
];

// ── Main screen ───────────────────────────────────────────────────────────────
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
    const NetworkDevicesScreen(),
    const AlertHistoryScreen(),
    const SslManagerScreen(),
    const ProjectsScreen(),
    const DtrMonitoringScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final bottomPadding = MediaQuery.of(context).padding.bottom;

    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _screens,
      ),
      bottomNavigationBar: _ScrollableNavBar(
        selectedIndex: _selectedIndex,
        onTap: (i) => setState(() => _selectedIndex = i),
        bottomPadding: bottomPadding,
      ),
    );
  }
}

// ── Scrollable nav bar widget ─────────────────────────────────────────────────
class _ScrollableNavBar extends StatefulWidget {
  final int selectedIndex;
  final ValueChanged<int> onTap;
  final double bottomPadding;

  const _ScrollableNavBar({
    required this.selectedIndex,
    required this.onTap,
    required this.bottomPadding,
  });

  @override
  State<_ScrollableNavBar> createState() => _ScrollableNavBarState();
}

class _ScrollableNavBarState extends State<_ScrollableNavBar> {
  final _scrollController = ScrollController();

  static const _itemWidth    = 76.0;
  static const _barHeight    = 64.0;
  static const _accent       = Color(0xFF3B82F6);
  static const _bgColor      = Color(0xFF181929);

  @override
  void didUpdateWidget(_ScrollableNavBar old) {
    super.didUpdateWidget(old);
    if (old.selectedIndex != widget.selectedIndex) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToSelected());
    }
  }

  void _scrollToSelected() {
    if (!_scrollController.hasClients) return;
    final viewportWidth = _scrollController.position.viewportDimension;
    final targetOffset =
        widget.selectedIndex * _itemWidth - viewportWidth / 2 + _itemWidth / 2;
    _scrollController.animateTo(
      targetOffset.clamp(
        _scrollController.position.minScrollExtent,
        _scrollController.position.maxScrollExtent,
      ),
      duration: const Duration(milliseconds: 280),
      curve: Curves.easeOutCubic,
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: _barHeight + widget.bottomPadding,
      decoration: const BoxDecoration(
        color: _bgColor,
        border: Border(
          top: BorderSide(color: Color(0xFF27272A), width: 1),
        ),
      ),
      child: SingleChildScrollView(
        controller: _scrollController,
        scrollDirection: Axis.horizontal,
        padding: EdgeInsets.only(
          left: 4,
          right: 4,
          bottom: widget.bottomPadding,
        ),
        child: Row(
          children: List.generate(_navItems.length, (i) {
            return _NavButton(
              item: _navItems[i],
              selected: i == widget.selectedIndex,
              width: _itemWidth,
              height: _barHeight,
              accent: _accent,
              onTap: () => widget.onTap(i),
            );
          }),
        ),
      ),
    );
  }
}

// ── Individual nav button ─────────────────────────────────────────────────────
class _NavButton extends StatelessWidget {
  final _NavItem item;
  final bool selected;
  final double width;
  final double height;
  final Color accent;
  final VoidCallback onTap;

  const _NavButton({
    required this.item,
    required this.selected,
    required this.width,
    required this.height,
    required this.accent,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: SizedBox(
        width: width,
        height: height,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Animated top indicator pill
            AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              curve: Curves.easeOutCubic,
              height: 3,
              width: selected ? 28 : 0,
              margin: const EdgeInsets.only(bottom: 5),
              decoration: BoxDecoration(
                gradient: selected
                    ? LinearGradient(
                        colors: [accent, accent.withValues(alpha: 0.4)],
                      )
                    : null,
                borderRadius: BorderRadius.circular(3),
              ),
            ),

            // Icon with animated switch
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 180),
              child: Icon(
                selected ? item.activeIcon : item.icon,
                key: ValueKey(selected),
                size: 22,
                color: selected ? accent : Colors.white24,
              ),
            ),

            const SizedBox(height: 3),

            // Label
            Text(
              item.label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
                color: selected ? accent : Colors.white24,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}
