import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../models/dtr_metrics.dart';
import '../models/dtr_log_entry.dart';
import '../providers/dashboard_provider.dart';
import 'dart:async';

// Real DTR API provider for basic metrics
final dtrRealMetricsProvider = FutureProvider<DtrMetrics>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  try {
    return await client.getDtrMetrics();
  } catch (e) {
    // Return mock metrics if API fails
    return DtrMetrics(
      activeUsers: 0,
      totalClockIns: 0,
      totalClockOuts: 0,
      lateArrivals: 0,
      overtimeHours: 0.0,
      systemHealthy: false,
      lastUpdated: DateTime.now(),
    );
  }
});

// Real DTR API provider for logs
final dtrRealLogsProvider = FutureProvider<List<DtrLogEntry>>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  try {
    return await client.getDtrLogs(limit: 50);
  } catch (e) {
    // Return empty list if API fails
    return [];
  }
});

// Real DTR API provider for system health
final dtrRealSystemHealthProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  try {
    return await client.getDtrSystemHealth();
  } catch (e) {
    // Return empty map if API fails
    return {
      'status': 'unhealthy',
      'message': 'Failed to connect to DTR API',
      'timestamp': DateTime.now().toIso8601String(),
    };
  }
});

// Combined provider for real-time DTR monitoring
final dtrRealTimeMonitoringProvider = StateNotifierProvider<DtrRealTimeNotifier, DtrRealTimeState>((ref) {
  return DtrRealTimeNotifier(ref);
});

class DtrRealTimeState {
  final DtrMetrics? metrics;
  final List<DtrLogEntry> logs;
  final Map<String, dynamic>? systemHealth;
  final bool isLoading;
  final String? error;
  final DateTime lastUpdated;

  DtrRealTimeState({
    this.metrics,
    this.logs = const [],
    this.systemHealth,
    this.isLoading = false,
    this.error,
    DateTime? lastUpdated,
  }) : lastUpdated = lastUpdated ?? DateTime.now();

  DtrRealTimeState copyWith({
    DtrMetrics? metrics,
    List<DtrLogEntry>? logs,
    Map<String, dynamic>? systemHealth,
    bool? isLoading,
    String? error,
    DateTime? lastUpdated,
  }) {
    return DtrRealTimeState(
      metrics: metrics ?? this.metrics,
      logs: logs ?? this.logs,
      systemHealth: systemHealth ?? this.systemHealth,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
      lastUpdated: lastUpdated ?? this.lastUpdated,
    );
  }
}

class DtrRealTimeNotifier extends StateNotifier<DtrRealTimeState> {
  final Ref _ref;
  Timer? _refreshTimer;

  DtrRealTimeNotifier(this._ref) : super(DtrRealTimeState()) {
    _initialize();
  }

  Future<void> _initialize() async {
    await refreshData();
    _startPeriodicRefresh();
  }

  void _startPeriodicRefresh() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(const Duration(minutes: 2), (_) {
      refreshData();
    });
  }

  Future<void> refreshData() async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      final client = _ref.read(apiClientProvider).value;
      if (client == null) {
        state = state.copyWith(
          isLoading: false,
          error: 'API client not initialized',
        );
        return;
      }

      // Fetch all data in parallel
      final results = await Future.wait([
        client.getDtrMetrics(),
        client.getDtrLogs(limit: 50),
        client.getDtrSystemHealth(),
      ]);

      final metrics = results[0] as DtrMetrics;
      final logs = results[1] as List<DtrLogEntry>;
      final systemHealth = results[2] as Map<String, dynamic>;

      state = state.copyWith(
        metrics: metrics,
        logs: logs,
        systemHealth: systemHealth,
        isLoading: false,
        lastUpdated: DateTime.now(),
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to refresh DTR data: $e',
      );
    }
  }

  Future<void> forceRefresh() async {
    await refreshData();
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }
}
