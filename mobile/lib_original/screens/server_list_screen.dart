import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/server_provider.dart';
import '../models/server.dart';
import 'server_detail_screen.dart';
import 'package:timeago/timeago.dart' as timeago;

class ServerListScreen extends ConsumerStatefulWidget {
  const ServerListScreen({super.key});

  @override
  ConsumerState<ServerListScreen> createState() => _ServerListScreenState();
}

class _ServerListScreenState extends ConsumerState<ServerListScreen> {
  String _searchQuery = '';

  @override
  Widget build(BuildContext context) {
    final serversAsync = ref.watch(serversProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0F0F23),
      appBar: AppBar(
        title: const Text('Servers'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(60),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              onChanged: (value) => setState(() => _searchQuery = value),
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'Search servers...',
                hintStyle: const TextStyle(color: Colors.white24),
                prefixIcon: const Icon(Icons.search, color: Colors.white24),
                filled: true,
                fillColor: const Color(0xFF181929),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
        ),
      ),
      body: serversAsync.when(
        data: (servers) {
          final filteredServers = servers.where((s) {
            final query = _searchQuery.toLowerCase();
            return s.name.toLowerCase().contains(query) || 
                   s.ipAddress.toLowerCase().contains(query);
          }).toList();

          return RefreshIndicator(
            onRefresh: () async => ref.refresh(serversProvider),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: filteredServers.length,
              itemBuilder: (context, index) {
                return _buildServerCard(filteredServers[index]);
              },
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildServerCard(Server server) {
    final isUp = server.lastStatus == 'UP';
    final statusColor = isUp ? Colors.green : (server.lastStatus == 'DOWN' ? Colors.red : Colors.grey);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF181929),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: statusColor.withOpacity(0.2)),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Flexible(
              child: Text(
                server.name,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (server.pinned)
              const Padding(
                padding: EdgeInsets.only(left: 8.0),
                child: Icon(Icons.push_pin, size: 14, color: Colors.blue),
              ),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(server.ipAddress, style: const TextStyle(color: Colors.white38, fontSize: 13)),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _buildMiniMetric(Icons.speed, '${server.cpuPercent?.toStringAsFixed(0) ?? '-'}%'),
                  const SizedBox(width: 12),
                  _buildMiniMetric(Icons.memory, '${server.ramPercent?.toStringAsFixed(0) ?? '-'}%'),
                  const SizedBox(width: 12),
                  if (server.latencyMs != null)
                    _buildMiniMetric(Icons.timer, '${server.latencyMs}ms'),
                ],
              ),
            )
          ],
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: statusColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                server.lastStatus,
                style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              server.lastChecked != null ? timeago.format(server.lastChecked!) : '-',
              style: const TextStyle(color: Colors.white24, fontSize: 10),
            ),
          ],
        ),
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => ServerDetailScreen(
                serverId: server.id,
                serverName: server.name,
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildMiniMetric(IconData icon, String value) {
    return Row(
      children: [
        Icon(icon, size: 12, color: Colors.white24),
        const SizedBox(width: 4),
        Text(value, style: const TextStyle(color: Colors.white70, fontSize: 11)),
      ],
    );
  }
}
