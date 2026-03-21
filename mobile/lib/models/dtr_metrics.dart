class DtrMetrics {
  final int activeUsers;
  final int totalClockIns;
  final int totalClockOuts;
  final int lateArrivals;
  final double overtimeHours;
  final bool systemHealthy;
  final DateTime lastUpdated;

  DtrMetrics({
    required this.activeUsers,
    required this.totalClockIns,
    required this.totalClockOuts,
    required this.lateArrivals,
    required this.overtimeHours,
    required this.systemHealthy,
    required this.lastUpdated,
  });

  factory DtrMetrics.fromJson(Map<String, dynamic> json) {
    return DtrMetrics(
      activeUsers: json['active_users'] ?? 0,
      totalClockIns: json['total_clock_ins'] ?? 0,
      totalClockOuts: json['total_clock_outs'] ?? 0,
      lateArrivals: json['late_arrivals'] ?? 0,
      overtimeHours: (json['overtime_hours'] ?? 0).toDouble(),
      systemHealthy: json['system_healthy'] ?? true,
      lastUpdated: DateTime.parse(json['last_updated'] ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'active_users': activeUsers,
      'total_clock_ins': totalClockIns,
      'total_clock_outs': totalClockOuts,
      'late_arrivals': lateArrivals,
      'overtime_hours': overtimeHours,
      'system_healthy': systemHealthy,
      'last_updated': lastUpdated.toIso8601String(),
    };
  }

  // Factory constructor for empty metrics when API is unavailable
  factory DtrMetrics.empty() {
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
