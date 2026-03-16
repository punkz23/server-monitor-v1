import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import '../providers/dtr_real_provider.dart';
import '../models/dtr_metrics.dart';

class DtrMetricsWidget extends ConsumerWidget {
  const DtrMetricsWidget({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dtrState = ref.watch(dtrRealTimeMonitoringProvider);
    final dtrNotifier = ref.read(dtrRealTimeMonitoringProvider.notifier);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF181929),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: const Color(0xFF3B82F6).withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'DTR Monitoring',
                style: GoogleFonts.inter(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              GestureDetector(
                onTap: () => dtrNotifier.forceRefresh(),
                child: Icon(
                  Icons.refresh,
                  color: Colors.grey[400],
                  size: 20,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (dtrState.isLoading)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF3B82F6)),
                  strokeWidth: 2,
                ),
              ),
            )
          else if (dtrState.error != null)
            _buildErrorState(dtrState.error!)
          else if (dtrState.metrics != null)
            _buildMetricsGrid(dtrState.metrics!)
          else
            _buildEmptyState(),
        ],
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFEF4444).withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: const Color(0xFFEF4444).withOpacity(0.3),
        ),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: Color(0xFFEF4444), size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'DTR API Error',
              style: GoogleFonts.inter(
                color: const Color(0xFFEF4444),
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Icon(
            Icons.fingerprint,
            color: Colors.grey[400],
            size: 32,
          ),
          const SizedBox(height: 8),
          Text(
            'No DTR data available',
            style: GoogleFonts.inter(
              color: Colors.grey[400],
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricsGrid(DtrMetrics metrics) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildMetricItem(
                'Active Users',
                metrics.activeUsers.toString(),
                Icons.people,
                const Color(0xFF10B981),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildMetricItem(
                'Clock-ins',
                metrics.totalClockIns.toString(),
                Icons.login,
                const Color(0xFF3B82F6),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildMetricItem(
                'Clock-outs',
                metrics.totalClockOuts.toString(),
                Icons.logout,
                const Color(0xFFF59E0B),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildMetricItem(
                'Late',
                metrics.lateArrivals.toString(),
                Icons.schedule,
                const Color(0xFFEF4444),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _buildSystemHealthIndicator(metrics),
      ],
    );
  }

  Widget _buildMetricItem(
    String label,
    String value,
    IconData icon,
    Color color,
  ) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: color.withOpacity(0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 16),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  label,
                  style: GoogleFonts.inter(
                    color: Colors.grey[400],
                    fontSize: 12,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: GoogleFonts.inter(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSystemHealthIndicator(DtrMetrics metrics) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: metrics.systemHealthy
            ? const Color(0xFF10B981).withOpacity(0.1)
            : const Color(0xFFEF4444).withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: metrics.systemHealthy
              ? const Color(0xFF10B981).withOpacity(0.3)
              : const Color(0xFFEF4444).withOpacity(0.3),
        ),
      ),
      child: Row(
        children: [
          Icon(
            metrics.systemHealthy ? Icons.check_circle : Icons.error,
            color: metrics.systemHealthy ? const Color(0xFF10B981) : const Color(0xFFEF4444),
            size: 20,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              metrics.systemHealthy ? 'System Healthy' : 'System Issues',
              style: GoogleFonts.inter(
                color: metrics.systemHealthy ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
