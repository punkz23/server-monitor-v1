import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import '../providers/server_provider.dart';
import '../models/server_detail.dart';
import 'package:intl/intl.dart';

class ServerDetailScreen extends ConsumerWidget {
  final int serverId;
  final String serverName;

  const ServerDetailScreen({
    super.key,
    required this.serverId,
    required this.serverName,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detailAsync = ref.watch(serverDetailProvider(serverId));

    return Scaffold(
      backgroundColor: const Color(0xFF0F0F23),
      appBar: AppBar(
        title: Text(serverName),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: detailAsync.when(
        data: (detail) => RefreshIndicator(
          onRefresh: () async => ref.refresh(serverDetailProvider(serverId)),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildRealtimeStats(detail),
                const SizedBox(height: 24),
                _buildChartSection('CPU Usage (%)', detail.historicalCpu, Colors.blue),
                const SizedBox(height: 24),
                _buildChartSection('RAM Usage (%)', detail.historicalRam, Colors.purple),
                const SizedBox(height: 24),
                if (detail.directoryWatch.isNotEmpty) ...[
                  _buildSectionTitle('Directory Watch'),
                  const SizedBox(height: 12),
                  ...detail.directoryWatch.map((dw) => _buildDirectoryWatchCard(dw)),
                  const SizedBox(height: 24),
                ] else if (detail.watchDirectory != null && detail.watchDirectory!.isNotEmpty) ...[
                  _buildDirectoryWatchSection(detail),
                  const SizedBox(height: 24),
                ],
                _buildServiceStatus(detail.services),
                const SizedBox(height: 24),
                if (detail.ssl.isNotEmpty) ...[
                  _buildSectionTitle('SSL Certificates'),
                  const SizedBox(height: 12),
                  ...detail.ssl.map((s) => _buildSslCard(s)),
                ],
              ],
            ),
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err', style: const TextStyle(color: Colors.white70))),
      ),
    );
  }

  Widget _buildRealtimeStats(ServerDetail detail) {
    final cpu = detail.metrics['cpu']?['usage_percent']?.toStringAsFixed(1) ?? '-';
    final ram = detail.metrics['ram']?['usage_percent']?.toStringAsFixed(1) ?? '-';
    final disk = detail.metrics['disk']?['usage_percent']?.toStringAsFixed(1) ?? '-';

    return Row(
      children: [
        _buildStatBox('CPU', '$cpu%', Colors.blue),
        const SizedBox(width: 12),
        _buildStatBox('RAM', '$ram%', Colors.purple),
        const SizedBox(width: 12),
        _buildStatBox('DISK', '$disk%', Colors.orange),
      ],
    );
  }

  Widget _buildStatBox(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF181929),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Text(label, style: const TextStyle(color: Colors.white38, fontSize: 12)),
            const SizedBox(height: 4),
            Text(value, style: TextStyle(color: color, fontSize: 18, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
    );
  }

  Widget _buildChartSection(String title, List<ResourcePoint> points, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionTitle(title),
        const SizedBox(height: 16),
        Container(
          height: 200,
          padding: const EdgeInsets.only(right: 16, top: 16),
          decoration: BoxDecoration(
            color: const Color(0xFF181929),
            borderRadius: BorderRadius.circular(16),
          ),
          child: points.isEmpty 
            ? const Center(child: Text('No historical data', style: TextStyle(color: Colors.white24)))
            : LineChart(
                LineChartData(
                  gridData: const FlGridData(show: false),
                  titlesData: const FlTitlesData(show: false),
                  borderData: FlBorderData(show: false),
                  lineBarsData: [
                    LineChartBarData(
                      spots: points.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value.value)).toList(),
                      isCurved: true,
                      color: color,
                      barWidth: 3,
                      isStrokeCapRound: true,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        color: color.withOpacity(0.1),
                      ),
                    ),
                  ],
                ),
              ),
        ),
      ],
    );
  }

  Widget _buildServiceStatus(List<ServiceStatus> services) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionTitle('Services'),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: const Color(0xFF181929),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            children: services.map((s) => ListTile(
              title: Text(s.name, style: const TextStyle(color: Colors.white, fontSize: 14)),
              trailing: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: (s.status == 'up' ? Colors.green : Colors.red).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  s.status.toUpperCase(),
                  style: TextStyle(
                    color: s.status == 'up' ? Colors.green : Colors.red,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            )).toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildSslCard(Map<String, dynamic> ssl) {
    final days = ssl['days_until_expiry'] ?? 0;
    final isCrit = days < 7;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF181929),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: (isCrit ? Colors.red : Colors.orange).withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(ssl['domain'] ?? 'Unknown Domain', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              Text('$days days left', style: TextStyle(color: isCrit ? Colors.red : Colors.orange, fontSize: 12)),
            ],
          ),
          const SizedBox(height: 4),
          Text('Issuer: ${ssl['issuer'] ?? 'Unknown'}', style: const TextStyle(color: Colors.white38, fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildDirectoryWatchCard(dynamic dwData) {
    // Check if it's a Map or already parsed (it's dynamic in model)
    final dw = dwData is Map ? dwData : {};
    final path = dw['path'] ?? 'Unknown Path';
    final folderName = dw['newest_folder_name'];
    final folderSize = dw['newest_folder_size_mb'];
    final lastModifiedStr = dw['newest_folder_last_modified'];
    final lastModified = lastModifiedStr != null ? DateTime.parse(lastModifiedStr) : null;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF181929),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.blue.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Path: $path', style: const TextStyle(color: Colors.white38, fontSize: 11)),
          const SizedBox(height: 8),
          folderName == null
              ? const Text('No folders detected', style: TextStyle(color: Colors.white24, fontSize: 14))
              : Column(
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.folder_open, color: Colors.blue, size: 16),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            folderName,
                            style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        _buildDirStat('Size', '${folderSize ?? 0} MB'),
                        _buildDirStat('Created', _formatDate(lastModified)),
                      ],
                    ),
                  ],
                ),
        ],
      ),
    );
  }

  Widget _buildDirectoryWatchSection(ServerDetail detail) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionTitle('Directory Watch'),
        const SizedBox(height: 4),
        Text('Monitoring: ${detail.watchDirectory}', style: const TextStyle(color: Colors.white38, fontSize: 12)),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF181929),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.blue.withOpacity(0.2)),
          ),
          child: detail.latestFolderName == null
              ? const Center(child: Text('No folders detected yet', style: TextStyle(color: Colors.white24)))
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.folder_open, color: Colors.blue, size: 20),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            detail.latestFolderName!,
                            style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        _buildDirStat('Files', '${detail.latestFolderFiles ?? 0}'),
                        _buildDirStat('Size', '${detail.latestFolderSizeMb ?? 0} MB'),
                        _buildDirStat('Created', _formatDate(detail.latestFolderCreated)),
                      ],
                    ),
                  ],
                ),
        ),
      ],
    );
  }

  Widget _buildDirStat(String label, String value) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: Colors.white38, fontSize: 11)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  String _formatDate(DateTime? date) {
    if (date == null) return 'Unknown';
    final now = DateTime.now();
    final difference = now.difference(date);
    
    if (difference.inSeconds < 60) {
      return 'just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else {
      return DateFormat('MMM dd, yyyy').format(date);
    }
  }
}
