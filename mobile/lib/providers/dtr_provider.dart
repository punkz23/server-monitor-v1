import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/dtr_model.dart';
import '../core/api_client.dart';
import 'dashboard_provider.dart';

final dtrAccuracyProvider = FutureProvider<DtrAccuracyData>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  try {
    // Use DTR API endpoints
    final r = await client.dtrDio.get('/dtr/accuracy-friction/');
    return DtrAccuracyData.fromJson(r.data['data']);
  } catch (e) {
    // Return mock data if API fails
    return DtrAccuracyData(
      totalSessions: 0,
      falseRejectionRate: 0.0,
      retryCountAvg: 0.0,
      livenessFailures: 0,
      manualOverrideRate: 0.0,
      alerts: {},
    );
  }
});

final dtrPerformanceProvider = FutureProvider<DtrPerformanceData>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  try {
    // Use DTR API endpoints
    final r = await client.dtrDio.get('/dtr/performance-latency/');
    return DtrPerformanceData.fromJson(r.data['data']);
  } catch (e) {
    // Return mock data if API fails
    return DtrPerformanceData(
      recognitionLatency: const DtrLatency(wifiAvg: 0.0, mobileAvg: 0.0),
      appStartupTime: 0.0,
      frameDropRate: 0.0,
      batteryDrainPerPunch: 0.0,
    );
  }
});

final dtrEnvironmentalProvider =
    FutureProvider<DtrEnvironmentalData>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  try {
    // Use DTR API endpoints
    final r = await client.dtrDio.get('/dtr/environmental-hardware/');
    return DtrEnvironmentalData.fromJson(r.data['data']);
  } catch (e) {
    // Return mock data if API fails
    return DtrEnvironmentalData(
      deviceFailures: {},
      locationFailures: {},
    );
  }
});

final dtrOperationalProvider =
    FutureProvider<DtrOperationalData>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  try {
    // Use DTR API endpoints
    final r = await client.dtrDio.get('/dtr/operational-security/');
    return DtrOperationalData.fromJson(r.data['data']);
  } catch (e) {
    // Return mock data if API fails
    return DtrOperationalData(
      geofencePrecision: const DtrGeofence(avgDistance: 0.0, precisionStatus: 'unknown'),
      syncPerformance: const DtrSyncPerf(avgSyncLag: 0.0, syncStatus: 'unknown'),
      apiHealth: const DtrApiHealth(errorRate: 0.0, healthStatus: 'unknown', totalRequests: 0),
      securityMetrics: const DtrSecurityMetrics(livenessSuccessRate: 0.0, spoofingAttemptsDetected: 0),
    );
  }
});

final dtrHeatmapProvider =
    FutureProvider<List<DtrHeatmapLocation>>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  try {
    // Use DTR API endpoints
    final r = await client.dtrDio.get('/dtr/heatmap/');
    final list = r.data['data'] as List<dynamic>? ?? [];
    return list.map((e) => DtrHeatmapLocation.fromJson(e)).toList();
  } catch (e) {
    // Return empty list if API fails
    return [];
  }
});
