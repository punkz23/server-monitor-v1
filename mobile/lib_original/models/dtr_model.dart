// DTR Biometric Monitoring — Data Models

// ── Accuracy & Friction ───────────────────────────────────────────────────────
class DtrAccuracyData {
  final int totalSessions;
  final double falseRejectionRate;
  final double retryCountAvg;
  final int livenessFailures;
  final double manualOverrideRate;
  final Map<String, bool> alerts;

  const DtrAccuracyData({
    required this.totalSessions,
    required this.falseRejectionRate,
    required this.retryCountAvg,
    required this.livenessFailures,
    required this.manualOverrideRate,
    required this.alerts,
  });

  factory DtrAccuracyData.fromJson(Map<String, dynamic> j) => DtrAccuracyData(
        totalSessions: j['total_sessions'] ?? 0,
        falseRejectionRate: (j['false_rejection_rate'] ?? 0).toDouble(),
        retryCountAvg: (j['retry_count_avg'] ?? 0).toDouble(),
        livenessFailures: j['liveness_failures'] ?? 0,
        manualOverrideRate: (j['manual_override_rate'] ?? 0).toDouble(),
        alerts: Map<String, bool>.from(j['alerts'] ?? {}),
      );
}

// ── Performance & Latency ────────────────────────────────────────────────────
class DtrLatency {
  final double wifiAvg;
  final double mobileAvg;
  const DtrLatency({required this.wifiAvg, required this.mobileAvg});
  factory DtrLatency.fromJson(Map<String, dynamic> j) => DtrLatency(
        wifiAvg: (j['wifi_avg'] ?? 0).toDouble(),
        mobileAvg: (j['mobile_avg'] ?? 0).toDouble(),
      );
}

class DtrPerformanceData {
  final DtrLatency recognitionLatency;
  final double appStartupTime;
  final double frameDropRate;
  final double batteryDrainPerPunch;

  const DtrPerformanceData({
    required this.recognitionLatency,
    required this.appStartupTime,
    required this.frameDropRate,
    required this.batteryDrainPerPunch,
  });

  factory DtrPerformanceData.fromJson(Map<String, dynamic> j) =>
      DtrPerformanceData(
        recognitionLatency:
            DtrLatency.fromJson(j['recognition_latency'] ?? {}),
        appStartupTime: (j['app_startup_time'] ?? 0).toDouble(),
        frameDropRate: (j['frame_drop_rate'] ?? 0).toDouble(),
        batteryDrainPerPunch: (j['battery_drain_per_punch'] ?? 0).toDouble(),
      );
}

// ── Environmental & Hardware ──────────────────────────────────────────────────
class DtrDeviceStats {
  final int totalSessions;
  final int failedSessions;
  final double failureRate;
  const DtrDeviceStats({
    required this.totalSessions,
    required this.failedSessions,
    required this.failureRate,
  });
  factory DtrDeviceStats.fromJson(Map<String, dynamic> j) => DtrDeviceStats(
        totalSessions: j['total_sessions'] ?? 0,
        failedSessions: j['failed_sessions'] ?? 0,
        failureRate: (j['failure_rate'] ?? 0).toDouble(),
      );
}

class DtrLocationStats {
  final int totalSessions;
  final int failedSessions;
  final double failureRate;
  final double avgGeofenceDistance;
  const DtrLocationStats({
    required this.totalSessions,
    required this.failedSessions,
    required this.failureRate,
    required this.avgGeofenceDistance,
  });
  factory DtrLocationStats.fromJson(Map<String, dynamic> j) => DtrLocationStats(
        totalSessions: j['total_sessions'] ?? 0,
        failedSessions: j['failed_sessions'] ?? 0,
        failureRate: (j['failure_rate'] ?? 0).toDouble(),
        avgGeofenceDistance: (j['avg_geofence_distance'] ?? 0).toDouble(),
      );
}

class DtrEnvironmentalData {
  final Map<String, DtrDeviceStats> deviceFailures;
  final Map<String, DtrLocationStats> locationFailures;

  const DtrEnvironmentalData({
    required this.deviceFailures,
    required this.locationFailures,
  });

  factory DtrEnvironmentalData.fromJson(Map<String, dynamic> j) {
    final devRaw = (j['device_failures'] as Map<String, dynamic>?) ?? {};
    final locRaw = (j['location_failures'] as Map<String, dynamic>?) ?? {};
    return DtrEnvironmentalData(
      deviceFailures: devRaw.map(
          (k, v) => MapEntry(k, DtrDeviceStats.fromJson(v))),
      locationFailures: locRaw.map(
          (k, v) => MapEntry(k, DtrLocationStats.fromJson(v))),
    );
  }
}

// ── Operational & Security ────────────────────────────────────────────────────
class DtrGeofence {
  final double avgDistance;
  final String precisionStatus;
  const DtrGeofence({required this.avgDistance, required this.precisionStatus});
  factory DtrGeofence.fromJson(Map<String, dynamic> j) => DtrGeofence(
        avgDistance: (j['avg_distance'] ?? 0).toDouble(),
        precisionStatus: j['precision_status'] ?? 'unknown',
      );
}

class DtrSyncPerf {
  final double avgSyncLag;
  final String syncStatus;
  const DtrSyncPerf({required this.avgSyncLag, required this.syncStatus});
  factory DtrSyncPerf.fromJson(Map<String, dynamic> j) => DtrSyncPerf(
        avgSyncLag: (j['avg_sync_lag'] ?? 0).toDouble(),
        syncStatus: j['sync_status'] ?? 'unknown',
      );
}

class DtrApiHealth {
  final double errorRate;
  final String healthStatus;
  final int totalRequests;
  const DtrApiHealth({
    required this.errorRate,
    required this.healthStatus,
    required this.totalRequests,
  });
  factory DtrApiHealth.fromJson(Map<String, dynamic> j) => DtrApiHealth(
        errorRate: (j['error_rate'] ?? 0).toDouble(),
        healthStatus: j['health_status'] ?? 'unknown',
        totalRequests: j['total_requests'] ?? 0,
      );
}

class DtrSecurityMetrics {
  final double livenessSuccessRate;
  final int spoofingAttemptsDetected;
  const DtrSecurityMetrics({
    required this.livenessSuccessRate,
    required this.spoofingAttemptsDetected,
  });
  factory DtrSecurityMetrics.fromJson(Map<String, dynamic> j) =>
      DtrSecurityMetrics(
        livenessSuccessRate: (j['liveness_success_rate'] ?? 0).toDouble(),
        spoofingAttemptsDetected: j['spoofing_attempts_detected'] ?? 0,
      );
}

class DtrOperationalData {
  final DtrGeofence geofencePrecision;
  final DtrSyncPerf syncPerformance;
  final DtrApiHealth apiHealth;
  final DtrSecurityMetrics securityMetrics;

  const DtrOperationalData({
    required this.geofencePrecision,
    required this.syncPerformance,
    required this.apiHealth,
    required this.securityMetrics,
  });

  factory DtrOperationalData.fromJson(Map<String, dynamic> j) =>
      DtrOperationalData(
        geofencePrecision:
            DtrGeofence.fromJson(j['geofence_precision'] ?? {}),
        syncPerformance:
            DtrSyncPerf.fromJson(j['sync_performance'] ?? {}),
        apiHealth: DtrApiHealth.fromJson(j['api_health'] ?? {}),
        securityMetrics:
            DtrSecurityMetrics.fromJson(j['security_metrics'] ?? {}),
      );
}

// ── Heatmap ───────────────────────────────────────────────────────────────────
class DtrHeatmapLocation {
  final String location;
  final double avgTimeToPunch; // ms
  final int totalPunches;
  final double failureRate;
  final String performanceColor;

  const DtrHeatmapLocation({
    required this.location,
    required this.avgTimeToPunch,
    required this.totalPunches,
    required this.failureRate,
    required this.performanceColor,
  });

  factory DtrHeatmapLocation.fromJson(Map<String, dynamic> j) =>
      DtrHeatmapLocation(
        location: j['location'] ?? 'Unknown',
        avgTimeToPunch: (j['avg_time_to_punch'] ?? 0).toDouble(),
        totalPunches: j['total_punches'] ?? 0,
        failureRate: (j['failure_rate'] ?? 0).toDouble(),
        performanceColor: j['performance_color'] ?? 'green',
      );
}
