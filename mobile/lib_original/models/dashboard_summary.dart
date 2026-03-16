class DashboardSummary {
  final int serversOnline;
  final int serversTotal;
  final int devicesOnline;
  final int alerts24h;
  final int criticalAlerts;
  final Map<String, TypeStatus> statusByType;
  final List<dynamic> topAlerts;
  final DateTime timestamp;

  DashboardSummary({
    required this.serversOnline,
    required this.serversTotal,
    required this.devicesOnline,
    required this.alerts24h,
    required this.criticalAlerts,
    required this.statusByType,
    required this.topAlerts,
    required this.timestamp,
  });

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    final summary = json['summary'] as Map<String, dynamic>;
    final statusByType = <String, TypeStatus>{};
    
    (json['status_by_type'] as Map<String, dynamic>).forEach((key, value) {
      statusByType[key] = TypeStatus.fromJson(value as Map<String, dynamic>);
    });

    return DashboardSummary(
      serversOnline: summary['servers_online'] ?? 0,
      serversTotal: summary['servers_total'] ?? 0,
      devicesOnline: summary['devices_online'] ?? 0,
      alerts24h: summary['alerts_24h'] ?? 0,
      criticalAlerts: summary['critical_alerts'] ?? 0,
      statusByType: statusByType,
      topAlerts: json['top_alerts'] ?? [],
      timestamp: DateTime.parse(json['timestamp']),
    );
  }
}

class TypeStatus {
  final int total;
  final int online;

  TypeStatus({required this.total, required this.online});

  factory TypeStatus.fromJson(Map<String, dynamic> json) {
    return TypeStatus(
      total: json['total'] ?? 0,
      online: json['online'] ?? 0,
    );
  }
}
