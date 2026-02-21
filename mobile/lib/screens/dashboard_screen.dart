import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/dashboard_provider.dart';
import 'package:intl/intl.dart';
import 'settings_screen.dart'; // Import the new settings screen

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summaryAsync = ref.watch(dashboardSummaryProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0F0F23),
      appBar: AppBar(
        title: const Text('ServerWatch'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings), // Settings icon
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const SettingsScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(dashboardSummaryProvider),
          ),
        ],
      ),
      body: summaryAsync.when(
        data: (summary) => RefreshIndicator(
          onRefresh: () async => ref.refresh(dashboardSummaryProvider),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildSummaryHeader(summary),
                const SizedBox(height: 24),
                _buildSectionTitle('Infrastructure Health'),
                const SizedBox(height: 12),
                _buildTypeBreakdown(summary),
                const SizedBox(height: 24),
                _buildSectionTitle('Recent Alerts'),
                const SizedBox(height: 12),
                _buildAlertList(summary.topAlerts),
              ],
            ),
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 48),
              const SizedBox(height: 16),
              Text('Error: $err', style: const TextStyle(color: Colors.white70)),
              ElevatedButton(
                onPressed: () => ref.refresh(dashboardSummaryProvider),
                child: const Text('Retry'),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 18,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  Widget _buildSummaryHeader(dynamic summary) {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      childAspectRatio: 1.5,
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      children: [
        _buildStatCard('Servers', '${summary.serversOnline}/${summary.serversTotal}', 
            summary.serversOnline == summary.serversTotal ? Colors.green : Colors.orange),
        _buildStatCard('Devices', '${summary.devicesOnline} Active', Colors.blue),
        _buildStatCard('24h Alerts', '${summary.alerts24h}', Colors.amber),
        _buildStatCard('Critical', '${summary.criticalAlerts}', 
            summary.criticalAlerts > 0 ? Colors.red : Colors.green),
      ],
    );
  }

  Widget _buildStatCard(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF181929),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(color: color, fontSize: 20, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildTypeBreakdown(dynamic summary) {
    return Column(
      children: summary.statusByType.entries.map<Widget>((entry) {
        final progress = entry.value.total > 0 ? entry.value.online / entry.value.total : 0.0;
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF181929),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(entry.key, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
                  Text('${entry.value.online}/${entry.value.total} UP', 
                      style: TextStyle(color: progress == 1.0 ? Colors.green : Colors.orange, fontSize: 12)),
                ],
              ),
              const SizedBox(height: 8),
              LinearProgressIndicator(
                value: progress.toDouble(),
                backgroundColor: Colors.white10,
                valueColor: AlwaysStoppedAnimation<Color>(progress == 1.0 ? Colors.green : Colors.orange),
                borderRadius: BorderRadius.circular(4),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildAlertList(List<dynamic> alerts) {
    if (alerts.isEmpty) {
      return const Center(child: Text('No recent alerts', style: TextStyle(color: Colors.white38)));
    }
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: alerts.length,
      itemBuilder: (context, index) {
        final alert = alerts[index];
        final isCrit = alert['severity'] == 'CRITICAL';
        return ListTile(
          contentPadding: EdgeInsets.zero,
          leading: Icon(
            isCrit ? Icons.warning : Icons.info_outline,
            color: isCrit ? Colors.red : Colors.blue,
          ),
          title: Text(alert['title'] ?? 'Unknown Alert', style: const TextStyle(color: Colors.white, fontSize: 14)),
          subtitle: Text(
            DateFormat('HH:mm - MMM dd').format(DateTime.parse(alert['created_at'])),
            style: const TextStyle(color: Colors.white38, fontSize: 12),
          ),
          trailing: const Icon(Icons.chevron_right, color: Colors.white24),
        );
      },
    );
  }
}
