import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/dtr_model.dart';
import '../providers/dtr_provider.dart';

// ── Colour helpers ────────────────────────────────────────────────────────────
const _bgPrimary = Color(0xFF0F0F23);
const _bgCard = Color(0xFF181929);
const _bgCard2 = Color(0xFF1E1F38);
const _green = Color(0xFF10B981);
const _amber = Color(0xFFF59E0B);
const _red = Color(0xFFEF4444);
const _purple = Color(0xFF8B5CF6);
const _blue = Color(0xFF3B82F6);

Color _thresholdColor(double v, double warnAt, double critAt,
    {bool reversed = false}) {
  if (reversed) {
    if (v >= warnAt) return _green;
    if (v >= critAt) return _amber;
    return _red;
  }
  if (v <= warnAt) return _green;
  if (v <= critAt) return _amber;
  return _red;
}

// ── Main screen ───────────────────────────────────────────────────────────────
class DtrMonitoringScreen extends ConsumerStatefulWidget {
  const DtrMonitoringScreen({super.key});

  @override
  ConsumerState<DtrMonitoringScreen> createState() =>
      _DtrMonitoringScreenState();
}

class _DtrMonitoringScreenState extends ConsumerState<DtrMonitoringScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;

  final _tabLabels = const [
    ('Overview', Icons.dashboard_outlined),
    ('Performance', Icons.bolt_outlined),
    ('Devices', Icons.phone_android_outlined),
    ('Locations', Icons.location_on_outlined),
    ('Security', Icons.shield_outlined),
  ];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: _tabLabels.length, vsync: this);
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  void _refreshAll() {
    ref.invalidate(dtrAccuracyProvider);
    ref.invalidate(dtrPerformanceProvider);
    ref.invalidate(dtrEnvironmentalProvider);
    ref.invalidate(dtrOperationalProvider);
    ref.invalidate(dtrHeatmapProvider);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgPrimary,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                ),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.fingerprint, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('DTR Monitor',
                    style:
                        TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                Text('Biometric Intelligence',
                    style:
                        TextStyle(fontSize: 10, color: Colors.white38)),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh all',
            onPressed: _refreshAll,
          ),
        ],
        bottom: TabBar(
          controller: _tabs,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          indicatorColor: _purple,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white38,
          labelStyle:
              const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
          tabs: _tabLabels
              .map((t) => Tab(
                    icon: Icon(t.$2, size: 16),
                    text: t.$1,
                    iconMargin: const EdgeInsets.only(bottom: 2),
                  ))
              .toList(),
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: const [
          _OverviewTab(),
          _PerformanceTab(),
          _DevicesTab(),
          _LocationsTab(),
          _SecurityTab(),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared widgets
// ─────────────────────────────────────────────────────────────────────────────

Widget _sectionLabel(String text) => Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Text(text.toUpperCase(),
          style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.2,
              color: Colors.white38)),
    );

Widget _card({required Widget child, Color? borderColor, EdgeInsets? padding}) =>
    Container(
      padding: padding ?? const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _bgCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
            color: borderColor ?? Colors.white.withOpacity(0.07), width: 1),
      ),
      child: child,
    );

Widget _kpiCard({
  required String label,
  required String value,
  required Color color,
  required String sub,
  required double barPct,
}) =>
    _card(
      borderColor: color.withOpacity(0.25),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: const TextStyle(
                  fontSize: 11, color: Colors.white54, fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          Text(value,
              style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: color,
                  height: 1)),
          const SizedBox(height: 4),
          Text(sub,
              style: const TextStyle(fontSize: 11, color: Colors.white38)),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: barPct.clamp(0.0, 1.0),
              backgroundColor: Colors.white10,
              valueColor: AlwaysStoppedAnimation<Color>(color),
              minHeight: 4,
            ),
          ),
        ],
      ),
    );

Widget _statRow(String label, String value, {Widget? trailing}) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: Colors.white54)),
          trailing ?? Text(value,
              style: const TextStyle(
                  fontSize: 13,
                  color: Colors.white,
                  fontWeight: FontWeight.w600)),
        ],
      ),
    );

Widget _chip(String label, Color color) => Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
          color: color.withOpacity(0.15),
          borderRadius: BorderRadius.circular(5),
          border: Border.all(color: color.withOpacity(0.3))),
      child: Text(label,
          style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: color,
              letterSpacing: 0.5)),
    );

Widget _asyncGuard<T>(
  AsyncValue<T> async,
  Widget Function(T data) builder,
  VoidCallback onRetry,
) =>
    async.when(
      data: builder,
      loading: () => const Center(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: CircularProgressIndicator(),
        ),
      ),
      error: (e, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.wifi_off_rounded, color: Colors.white24, size: 42),
              const SizedBox(height: 12),
              Text('$e',
                  style:
                      const TextStyle(color: Colors.white38, fontSize: 12),
                  textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
    );

// ─────────────────────────────────────────────────────────────────────────────
// Tab 1 — Overview
// ─────────────────────────────────────────────────────────────────────────────
class _OverviewTab extends ConsumerWidget {
  const _OverviewTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(dtrAccuracyProvider);

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(dtrAccuracyProvider),
      child: _asyncGuard<DtrAccuracyData>(
        async,
        (d) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _sectionLabel('Accuracy & Friction · Last 24 h'),

            // Liveness spike banner
            if (d.alerts['liveness_spike'] == true)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: _red.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: _red.withOpacity(0.35)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.electric_bolt, color: Color(0xFFEF4444), size: 16),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Liveness spike detected — investigate immediately',
                        style: TextStyle(
                            color: Color(0xFFEF4444),
                            fontSize: 12,
                            fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),

            // Sessions card (plain info)
            _kpiCard(
              label: 'TOTAL SESSIONS',
              value: '${d.totalSessions}',
              color: _blue,
              sub: 'All punch attempts',
              barPct: 1.0,
            ),
            const SizedBox(height: 10),

            Row(
              children: [
                Expanded(
                  child: _kpiCard(
                    label: 'FALSE REJECTION',
                    value: '${d.falseRejectionRate.toStringAsFixed(1)}%',
                    color: _thresholdColor(d.falseRejectionRate, 2, 5),
                    sub: 'Target < 2%',
                    barPct: d.falseRejectionRate / 10,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _kpiCard(
                    label: 'AVG RETRIES',
                    value: '${d.retryCountAvg.toStringAsFixed(2)}×',
                    color: _thresholdColor(d.retryCountAvg, 1.5, 3),
                    sub: 'Target < 1.5×',
                    barPct: d.retryCountAvg / 5,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            Row(
              children: [
                Expanded(
                  child: _kpiCard(
                    label: 'LIVENESS FAILURES',
                    value: '${d.livenessFailures}',
                    color: d.livenessFailures > 10 ? _red : _green,
                    sub: 'Spoofing blocked',
                    barPct: (d.livenessFailures / 50).clamp(0, 1),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _kpiCard(
                    label: 'MANUAL OVERRIDE',
                    value: '${d.manualOverrideRate.toStringAsFixed(1)}%',
                    color: _thresholdColor(d.manualOverrideRate, 5, 10),
                    sub: 'Target < 5%',
                    barPct: d.manualOverrideRate / 20,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            _sectionLabel('Alert Flags'),
            _card(
              child: Column(
                children: d.alerts.entries.map((e) {
                  final isActive = e.value;
                  return _statRow(
                    e.key.replaceAll('_', ' ').toUpperCase(),
                    '',
                    trailing: _chip(
                      isActive ? '⚡ Active' : '✅ Clear',
                      isActive ? _red : _green,
                    ),
                  );
                }).toList(),
              ),
            ),
          ],
        ),
        () => ref.invalidate(dtrAccuracyProvider),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 2 — Performance
// ─────────────────────────────────────────────────────────────────────────────
class _PerformanceTab extends ConsumerWidget {
  const _PerformanceTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(dtrPerformanceProvider);

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(dtrPerformanceProvider),
      child: _asyncGuard<DtrPerformanceData>(
        async,
        (d) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _sectionLabel('Recognition Latency'),
            _card(
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: _latencyTile(
                          label: '📶 WiFi',
                          ms: d.recognitionLatency.wifiAvg,
                          target: 1000,
                          color: _green,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _latencyTile(
                          label: '📱 4G',
                          ms: d.recognitionLatency.mobileAvg,
                          target: 2000,
                          color: _amber,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _LatencyBarChart(
                    wifi: d.recognitionLatency.wifiAvg,
                    mobile: d.recognitionLatency.mobileAvg,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            _sectionLabel('App Performance'),
            _card(
              child: Column(
                children: [
                  _perfRow(
                    label: 'App Startup Time',
                    value: '${d.appStartupTime.toStringAsFixed(0)} ms',
                    color: _thresholdColor(d.appStartupTime, 3000, 6000),
                    chipLabel: d.appStartupTime < 3000 ? 'Good' : d.appStartupTime < 6000 ? 'Slow' : 'Critical',
                  ),
                  const Divider(color: Colors.white10, height: 1),
                  _perfRow(
                    label: 'Frame Drop Rate',
                    value: '${d.frameDropRate.toStringAsFixed(1)}%',
                    color: _thresholdColor(d.frameDropRate, 5, 15),
                    chipLabel: d.frameDropRate < 5 ? 'Smooth' : d.frameDropRate < 15 ? 'Jank' : 'Critical',
                  ),
                  const Divider(color: Colors.white10, height: 1),
                  _perfRow(
                    label: 'Battery / Punch',
                    value: '${d.batteryDrainPerPunch.toStringAsFixed(2)}%',
                    color: _thresholdColor(d.batteryDrainPerPunch, 1, 3),
                    chipLabel: d.batteryDrainPerPunch < 1 ? 'Good' : d.batteryDrainPerPunch < 3 ? 'High' : 'Critical',
                  ),
                ],
              ),
            ),
          ],
        ),
        () => ref.invalidate(dtrPerformanceProvider),
      ),
    );
  }

  Widget _latencyTile({
    required String label,
    required double ms,
    required double target,
    required Color color,
  }) {
    final ok = ms <= target;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _bgCard2,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style:
                  const TextStyle(fontSize: 11, color: Colors.white54)),
          const SizedBox(height: 6),
          Text('${ms.toStringAsFixed(0)} ms',
              style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                  color: color)),
          const SizedBox(height: 4),
          _chip(ok ? '✅ On target' : '⚠ Slow', ok ? _green : _amber),
        ],
      ),
    );
  }

  Widget _perfRow({
    required String label,
    required String value,
    required Color color,
    required String chipLabel,
  }) =>
      Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
                child: Text(label,
                    style: const TextStyle(fontSize: 13, color: Colors.white70))),
            const SizedBox(width: 8),
            Text(value,
                style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: color)),
            const SizedBox(width: 8),
            _chip(chipLabel, color),
          ],
        ),
      );
}

class _LatencyBarChart extends StatelessWidget {
  final double wifi;
  final double mobile;
  const _LatencyBarChart({required this.wifi, required this.mobile});

  @override
  Widget build(BuildContext context) {
    final max = [wifi, mobile, 3000].reduce((a, b) => a > b ? a : b);
    return SizedBox(
      height: 160,
      child: BarChart(
        BarChartData(
          maxY: max * 1.2,
          barGroups: [
            _bar(0, wifi, _green),
            _bar(1, mobile, _amber),
          ],
          titlesData: FlTitlesData(
            leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (v, _) {
                  final labels = ['WiFi', '4G'];
                  final idx = v.toInt();
                  if (idx < 0 || idx >= labels.length) return const SizedBox();
                  return Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Text(labels[idx],
                        style: const TextStyle(
                            fontSize: 11, color: Colors.white54)),
                  );
                },
              ),
            ),
          ),
          borderData: FlBorderData(show: false),
          gridData: const FlGridData(show: false),
        ),
      ),
    );
  }

  BarChartGroupData _bar(int x, double y, Color color) => BarChartGroupData(
        x: x,
        barRods: [
          BarChartRodData(
            toY: y,
            color: color.withOpacity(0.8),
            width: 36,
            borderRadius: BorderRadius.circular(6),
          ),
        ],
      );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 3 — Devices
// ─────────────────────────────────────────────────────────────────────────────
class _DevicesTab extends ConsumerWidget {
  const _DevicesTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(dtrEnvironmentalProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(dtrEnvironmentalProvider),
      child: _asyncGuard<DtrEnvironmentalData>(
        async,
        (d) {
          final entries = d.deviceFailures.entries.toList()
            ..sort((a, b) =>
                b.value.failureRate.compareTo(a.value.failureRate));

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _sectionLabel('Device Failure Rates · ranked by failure %'),
              if (entries.isEmpty)
                _card(
                  child: const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Text('No device failures recorded',
                          style: TextStyle(color: Colors.white38)),
                    ),
                  ),
                )
              else
                _card(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 8),
                  child: Column(
                    children: entries.asMap().entries.map((e) {
                      final idx = e.key;
                      final device = e.value.key;
                      final stats = e.value.value;
                      final color = _thresholdColor(
                          stats.failureRate, 5, 15);
                      return _DeviceRow(
                        rank: idx + 1,
                        name: device,
                        failedSessions: stats.failedSessions,
                        totalSessions: stats.totalSessions,
                        failureRate: stats.failureRate,
                        color: color,
                      );
                    }).toList(),
                  ),
                ),
            ],
          );
        },
        () => ref.invalidate(dtrEnvironmentalProvider),
      ),
    );
  }
}

class _DeviceRow extends StatelessWidget {
  final int rank;
  final String name;
  final int failedSessions;
  final int totalSessions;
  final double failureRate;
  final Color color;

  const _DeviceRow({
    required this.rank,
    required this.name,
    required this.failedSessions,
    required this.totalSessions,
    required this.failureRate,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(6),
                ),
                alignment: Alignment.center,
                child: Text('$rank',
                    style: const TextStyle(
                        fontSize: 10,
                        color: Colors.white38,
                        fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(name,
                    style: const TextStyle(
                        fontSize: 13,
                        color: Colors.white,
                        fontWeight: FontWeight.w500),
                    overflow: TextOverflow.ellipsis),
              ),
              Text('$failedSessions/$totalSessions',
                  style:
                      const TextStyle(fontSize: 11, color: Colors.white38)),
              const SizedBox(width: 8),
              _chip('${failureRate.toStringAsFixed(1)}%', color),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (failureRate / 100).clamp(0.0, 1.0),
              backgroundColor: Colors.white10,
              valueColor: AlwaysStoppedAnimation<Color>(color),
              minHeight: 5,
            ),
          ),
          if (rank < 999) // always show divider except last
            const Divider(color: Colors.white10, height: 16),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 4 — Locations
// ─────────────────────────────────────────────────────────────────────────────
class _LocationsTab extends ConsumerWidget {
  const _LocationsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final envAsync = ref.watch(dtrEnvironmentalProvider);
    final hmAsync = ref.watch(dtrHeatmapProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(dtrEnvironmentalProvider);
        ref.invalidate(dtrHeatmapProvider);
      },
      child: _asyncGuard<DtrEnvironmentalData>(
        envAsync,
        (d) {
          final entries = d.locationFailures.entries.toList()
            ..sort((a, b) =>
                b.value.failureRate.compareTo(a.value.failureRate));

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _sectionLabel('Location Failure Rates'),
              if (entries.isEmpty)
                _card(
                  child: const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Text('No location failures recorded',
                          style: TextStyle(color: Colors.white38)),
                    ),
                  ),
                )
              else
                _card(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 8),
                  child: Column(
                    children: entries.asMap().entries.map((e) {
                      final idx = e.key;
                      final loc = e.value.key;
                      final stats = e.value.value;
                      final color =
                          _thresholdColor(stats.failureRate, 5, 15);
                      return _LocationRow(
                        rank: idx + 1,
                        name: loc.isEmpty ? '(unnamed)' : loc,
                        failedSessions: stats.failedSessions,
                        totalSessions: stats.totalSessions,
                        failureRate: stats.failureRate,
                        avgGeofenceDistance: stats.avgGeofenceDistance,
                        color: color,
                      );
                    }).toList(),
                  ),
                ),
              const SizedBox(height: 20),

              // Heatmap tiles
              _sectionLabel('Punch Zone Heatmap'),
              hmAsync.when(
                data: (locs) => locs.isEmpty
                    ? _card(
                        child: const Center(
                          child: Padding(
                            padding: EdgeInsets.all(24),
                            child: Text('No heatmap data yet',
                                style: TextStyle(color: Colors.white38)),
                          ),
                        ),
                      )
                    : Wrap(
                        spacing: 10,
                        runSpacing: 10,
                        children:
                            locs.map((l) => _HeatmapTile(loc: l)).toList(),
                      ),
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (e, _) => _card(
                  child: Text('$e',
                      style:
                          const TextStyle(color: Colors.white38, fontSize: 12)),
                ),
              ),
            ],
          );
        },
        () {
          ref.invalidate(dtrEnvironmentalProvider);
          ref.invalidate(dtrHeatmapProvider);
        },
      ),
    );
  }
}

class _LocationRow extends StatelessWidget {
  final int rank;
  final String name;
  final int failedSessions;
  final int totalSessions;
  final double failureRate;
  final double avgGeofenceDistance;
  final Color color;

  const _LocationRow({
    required this.rank,
    required this.name,
    required this.failedSessions,
    required this.totalSessions,
    required this.failureRate,
    required this.avgGeofenceDistance,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(6),
                ),
                alignment: Alignment.center,
                child: Text('$rank',
                    style: const TextStyle(
                        fontSize: 10,
                        color: Colors.white38,
                        fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(name,
                    style: const TextStyle(
                        fontSize: 13,
                        color: Colors.white,
                        fontWeight: FontWeight.w500),
                    overflow: TextOverflow.ellipsis),
              ),
              _chip('${avgGeofenceDistance.toStringAsFixed(0)}m geo', _blue),
              const SizedBox(width: 6),
              _chip('${failureRate.toStringAsFixed(1)}%', color),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (failureRate / 100).clamp(0.0, 1.0),
              backgroundColor: Colors.white10,
              valueColor: AlwaysStoppedAnimation<Color>(color),
              minHeight: 5,
            ),
          ),
          const Divider(color: Colors.white10, height: 16),
        ],
      ),
    );
  }
}

class _HeatmapTile extends StatelessWidget {
  final DtrHeatmapLocation loc;
  const _HeatmapTile({required this.loc});

  @override
  Widget build(BuildContext context) {
    final secs = loc.avgTimeToPunch / 1000;
    final Color tileColor;
    final String emoji;
    if (secs < 2) {
      tileColor = const Color(0xFF065F46);
      emoji = '🟢';
    } else if (secs < 5) {
      tileColor = const Color(0xFF78350F);
      emoji = '🟡';
    } else {
      tileColor = const Color(0xFF7F1D1D);
      emoji = '🔴';
    }

    return Container(
      width: 140,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: tileColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$emoji ${loc.location}',
              style: const TextStyle(
                  fontSize: 12,
                  color: Colors.white,
                  fontWeight: FontWeight.w600),
              overflow: TextOverflow.ellipsis),
          const SizedBox(height: 6),
          Text('${secs.toStringAsFixed(1)} s',
              style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                  color: Colors.white)),
          Text('${loc.totalPunches} punches',
              style: const TextStyle(
                  fontSize: 11, color: Colors.white54)),
          Text('${loc.failureRate.toStringAsFixed(1)}% fail',
              style: const TextStyle(
                  fontSize: 11, color: Colors.white54)),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 5 — Security
// ─────────────────────────────────────────────────────────────────────────────
class _SecurityTab extends ConsumerWidget {
  const _SecurityTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(dtrOperationalProvider);

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(dtrOperationalProvider),
      child: _asyncGuard<DtrOperationalData>(
        async,
        (d) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _sectionLabel('Geofence Precision'),
            _card(
              borderColor: (d.geofencePrecision.precisionStatus == 'good'
                      ? _green
                      : _amber)
                  .withOpacity(0.25),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Avg Distance from Zone',
                          style: TextStyle(
                              fontSize: 12, color: Colors.white54)),
                      _chip(
                        d.geofencePrecision.precisionStatus == 'good'
                            ? '✅ Precise'
                            : '⚠ Off-zone',
                        d.geofencePrecision.precisionStatus == 'good'
                            ? _green
                            : _amber,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${d.geofencePrecision.avgDistance.toStringAsFixed(0)} m',
                    style: TextStyle(
                      fontSize: 36,
                      fontWeight: FontWeight.w800,
                      color: d.geofencePrecision.precisionStatus == 'good'
                          ? _green
                          : _amber,
                    ),
                  ),
                  const Text('Target: < 50 m',
                      style: TextStyle(fontSize: 11, color: Colors.white38)),
                ],
              ),
            ),
            const SizedBox(height: 12),

            _sectionLabel('Sync Performance'),
            _card(
              borderColor: (d.syncPerformance.syncStatus == 'good'
                      ? _green
                      : _amber)
                  .withOpacity(0.25),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Avg Sync Lag',
                          style: TextStyle(
                              fontSize: 12, color: Colors.white54)),
                      _chip(
                        d.syncPerformance.syncStatus == 'good'
                            ? '✅ Fast'
                            : '⚠ Slow',
                        d.syncPerformance.syncStatus == 'good'
                            ? _green
                            : _amber,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${d.syncPerformance.avgSyncLag.toStringAsFixed(1)} s',
                    style: TextStyle(
                      fontSize: 36,
                      fontWeight: FontWeight.w800,
                      color: d.syncPerformance.syncStatus == 'good'
                          ? _green
                          : _amber,
                    ),
                  ),
                  const Text('Target: < 30 s',
                      style: TextStyle(fontSize: 11, color: Colors.white38)),
                ],
              ),
            ),
            const SizedBox(height: 12),

            _sectionLabel('API Health'),
            _card(
              borderColor: _thresholdColor(d.apiHealth.errorRate, 5, 15)
                  .withOpacity(0.25),
              child: Column(
                children: [
                  _statRow('Error Rate',
                      '${d.apiHealth.errorRate.toStringAsFixed(1)}%',
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('${d.apiHealth.errorRate.toStringAsFixed(1)}%',
                              style: TextStyle(
                                  fontWeight: FontWeight.w600,
                                  color: _thresholdColor(
                                      d.apiHealth.errorRate, 5, 15))),
                          const SizedBox(width: 8),
                          _chip(
                            d.apiHealth.healthStatus == 'healthy'
                                ? '✅ Healthy'
                                : d.apiHealth.errorRate < 15
                                    ? '⚠ Degraded'
                                    : '🔴 Critical',
                            _thresholdColor(d.apiHealth.errorRate, 5, 15),
                          ),
                        ],
                      )),
                  const Divider(color: Colors.white10, height: 1),
                  _statRow('Total Requests', '${d.apiHealth.totalRequests}'),
                ],
              ),
            ),
            const SizedBox(height: 12),

            _sectionLabel('Anti-Spoofing'),
            _card(
              borderColor: _purple.withOpacity(0.25),
              child: Column(
                children: [
                  _statRow(
                    'Liveness Success Rate',
                    '${d.securityMetrics.livenessSuccessRate}%',
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '${d.securityMetrics.livenessSuccessRate}%',
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            color: _thresholdColor(
                              d.securityMetrics.livenessSuccessRate,
                              90,
                              70,
                              reversed: true,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Divider(color: Colors.white10, height: 1),
                  _statRow(
                    'Spoofing Attempts Detected',
                    '',
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '${d.securityMetrics.spoofingAttemptsDetected}',
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 18,
                            color: d.securityMetrics.spoofingAttemptsDetected >
                                    0
                                ? _red
                                : _green,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        () => ref.invalidate(dtrOperationalProvider),
      ),
    );
  }
}
