import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/ssl_provider.dart';
import '../models/ssl_certificate.dart';
import 'package:intl/intl.dart';
import 'package:timeago/timeago.dart' as timeago;

class SslManagerScreen extends ConsumerWidget {
  const SslManagerScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sslAsync = ref.watch(sslCertificatesProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0F0F23),
      appBar: AppBar(
        title: const Text('SSL Manager'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(sslCertificatesProvider),
          ),
        ],
      ),
      body: sslAsync.when(
        data: (certs) {
          if (certs.isEmpty) {
            return const Center(child: Text('No certificates monitored', style: TextStyle(color: Colors.white24)));
          }

          // Sort by days remaining
          final sortedCerts = [...certs]..sort((a, b) => a.daysUntilExpiry.compareTo(b.daysUntilExpiry));

          return RefreshIndicator(
            onRefresh: () async => ref.refresh(sslCertificatesProvider),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: sortedCerts.length,
              itemBuilder: (context, index) {
                return _buildSslCard(sortedCerts[index]);
              },
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err', style: const TextStyle(color: Colors.white70))),
      ),
    );
  }

  Widget _buildSslCard(SslCertificate cert) {
    final status = cert.status;
    final statusColor = status == 'expired' || status == 'critical' 
        ? Colors.red 
        : (status == 'warning' ? Colors.orange : Colors.green);

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF181929),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: statusColor.withOpacity(0.2)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        cert.domain,
                        style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      if (cert.serverName != null)
                        Text(cert.serverName!, style: const TextStyle(color: Colors.white38, fontSize: 12)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '${cert.daysUntilExpiry} days',
                    style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                _buildInfoColumn('Issuer', cert.issuer ?? 'Unknown'),
                _buildInfoColumn('Expires', cert.expiresAt != null ? DateFormat('MMM dd, yyyy').format(cert.expiresAt!) : 'Unknown'),
              ],
            ),
            const SizedBox(height: 16),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: _calculateProgress(cert.daysUntilExpiry),
                backgroundColor: Colors.white10,
                valueColor: AlwaysStoppedAnimation<Color>(statusColor),
                minHeight: 6,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Checked: ${cert.lastChecked != null ? timeago.format(cert.lastChecked!) : "-"}',
                  style: const TextStyle(color: Colors.white24, fontSize: 10),
                ),
                if (status == 'expired' || status == 'critical')
                  const Icon(Icons.warning_amber_rounded, color: Colors.red, size: 16),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildInfoColumn(String label, String value) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: Colors.white38, fontSize: 11)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w500), overflow: TextOverflow.ellipsis),
        ],
      ),
    );
  }

  double _calculateProgress(int days) {
    if (days <= 0) return 0.0;
    if (days >= 90) return 1.0;
    return days / 90.0; // Assume 90 days is a "full" cycle for visual purposes
  }
}
