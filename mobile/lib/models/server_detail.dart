class ServerDetail {
  final int id;
  final String name;
  final String ipAddress;
  final Map<String, dynamic> metrics;
  final List<ResourcePoint> historicalCpu;
  final List<ResourcePoint> historicalRam;
  final List<dynamic> ssl;
  final List<dynamic> directoryWatch;
  final List<ServiceStatus> services;

  // New Directory Watch Fields
  final String? watchDirectory;
  final String? latestFolderName;
  final int? latestFolderFiles;
  final int? latestFolderSizeMb;
  final DateTime? latestFolderCreated;

  ServerDetail({
    required this.id,
    required this.name,
    required this.ipAddress,
    required this.metrics,
    required this.historicalCpu,
    required this.historicalRam,
    required this.ssl,
    required this.directoryWatch,
    required this.services,
    this.watchDirectory,
    this.latestFolderName,
    this.latestFolderFiles,
    this.latestFolderSizeMb,
    this.latestFolderCreated,
  });

  factory ServerDetail.fromJson(Map<String, dynamic> json) {
    final historical = json['historical'] as Map<String, dynamic>? ?? {};
    final server = json['server'] as Map<String, dynamic>? ?? {};
    
    return ServerDetail(
      id: json['server_id'] ?? server['id'] ?? 0,
      name: json['server_name'] ?? server['name'] ?? '',
      ipAddress: json['ip_address'] ?? server['ip_address'] ?? '',
      metrics: json['metrics'] ?? {},
      historicalCpu: _parsePoints(historical['cpu']),
      historicalRam: _parsePoints(historical['ram']),
      ssl: json['db_ssl'] ?? [],
      directoryWatch: json['directory_watch'] ?? [],
      services: (json['services'] as List? ?? [])
          .map((s) => ServiceStatus.fromJson(s))
          .toList(),
      watchDirectory: server['watch_directory'],
      latestFolderName: server['latest_folder_name'],
      latestFolderFiles: server['latest_folder_files'],
      latestFolderSizeMb: server['latest_folder_size_mb'],
      latestFolderCreated: server['latest_folder_created'] != null 
          ? DateTime.parse(server['latest_folder_created']) 
          : null,
    );
  }

  static List<ResourcePoint> _parsePoints(dynamic data) {
    if (data == null || data is! List) return [];
    return data.map((p) => ResourcePoint.fromJson(p)).toList();
  }
}

class ResourcePoint {
  final DateTime timestamp;
  final double value;

  ResourcePoint({required this.timestamp, required this.value});

  factory ResourcePoint.fromJson(Map<String, dynamic> json) {
    return ResourcePoint(
      timestamp: DateTime.parse(json['x']),
      value: (json['y'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class ServiceStatus {
  final String name;
  final String status;

  ServiceStatus({required this.name, required this.status});

  factory ServiceStatus.fromJson(Map<String, dynamic> json) {
    return ServiceStatus(
      name: json['name'] ?? '',
      status: json['status'] ?? 'down',
    );
  }
}
