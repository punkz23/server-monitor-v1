import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:async';
import '../core/api_client.dart';
import '../models/dtr_metrics.dart';
import '../models/dtr_log_entry.dart';

class DtrMonitoringState {
  final DtrMetrics? metrics;
  final List<DtrLogEntry> logs;
  final bool isLoading;
  final String? error;
  final DateTime lastUpdated;

  DtrMonitoringState({
    this.metrics,
    this.logs = const [],
    this.isLoading = false,
    this.error,
    DateTime? lastUpdated,
  }) : lastUpdated = lastUpdated ?? DateTime.now();

  DtrMonitoringState copyWith({
    DtrMetrics? metrics,
    List<DtrLogEntry>? logs,
    bool? isLoading,
    String? error,
    DateTime? lastUpdated,
  }) {
    return DtrMonitoringState(
      metrics: metrics ?? this.metrics,
      logs: logs ?? this.logs,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
      lastUpdated: lastUpdated ?? this.lastUpdated,
    );
  }
}

class DtrMonitoringNotifier extends StateNotifier<DtrMonitoringState> {
  final Ref _ref;
  Timer? _refreshTimer;

  DtrMonitoringNotifier(this._ref) : super(DtrMonitoringState()) {
    _initialize();
  }

  Future<void> _initialize() async {
    await refreshData();
    _startPeriodicRefresh();
  }

  void _startPeriodicRefresh() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(const Duration(minutes: 5), (_) {
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

      // Fetch metrics and logs in parallel
      final results = await Future.wait([
        _fetchMetrics(client),
        _fetchLogs(client),
      ]);

      final metrics = results[0] as DtrMetrics?;
      final logs = results[1] as List<DtrLogEntry>;

      state = state.copyWith(
        metrics: metrics,
        logs: logs,
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

  Future<DtrMetrics?> _fetchMetrics(ApiClient client) async {
    try {
      return await client.getDtrMetrics();
    } catch (e) {
      // Create mock metrics if API fails
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
  }

  Future<List<DtrLogEntry>> _fetchLogs(ApiClient client) async {
    try {
      return await client.getDtrLogs(limit: 50);
    } catch (e) {
      // Return empty list if API fails
      return [];
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

// Provider for DTR monitoring
final dtrMonitoringProvider = StateNotifierProvider<DtrMonitoringNotifier, DtrMonitoringState>((ref) {
  return DtrMonitoringNotifier(ref);
});

// Provider for DTR metrics only
final dtrMetricsProvider = Provider<DtrMetrics?>((ref) {
  return ref.watch(dtrMonitoringProvider).metrics;
});

// Provider for DTR logs only
final dtrLogsProvider = Provider<List<DtrLogEntry>>((ref) {
  return ref.watch(dtrMonitoringProvider).logs;
});

// Provider for loading state
final dtrLoadingProvider = Provider<bool>((ref) {
  return ref.watch(dtrMonitoringProvider).isLoading;
});

// Provider for error state
final dtrErrorProvider = Provider<String?>((ref) {
  return ref.watch(dtrMonitoringProvider).error;
});
