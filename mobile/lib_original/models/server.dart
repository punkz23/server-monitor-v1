class Server {
  final int id;
  final String name;
  final bool pinned;
  final String tags;
  final String serverType;
  final String serverTypeDisplay;
  final String ipAddress;
  final int port;
  final String lastStatus;
  final String lastStatusDisplay;
  final bool? lastHttpOk;
  final double? cpuPercent;
  final double? ramPercent;
  final int? latencyMs;
  final DateTime? lastChecked;

  // Directory Watch fields
  final String? watchDirectory;
  final String? latestFolderName;
  final int? latestFolderFiles;
  final int? latestFolderSizeMb;
  final DateTime? latestFolderCreated;

  Server({
    required this.id,
    required this.name,
    required this.pinned,
    required this.tags,
    required this.serverType,
    required this.serverTypeDisplay,
    required this.ipAddress,
    required this.port,
    required this.lastStatus,
    required this.lastStatusDisplay,
    this.lastHttpOk,
    this.cpuPercent,
    this.ramPercent,
    this.latencyMs,
    this.lastChecked,
    this.watchDirectory,
    this.latestFolderName,
    this.latestFolderFiles,
    this.latestFolderSizeMb,
    this.latestFolderCreated,
  });

  factory Server.fromJson(Map<String, dynamic> json) {
    return Server(
      id: json['id'],
      name: json['name'],
      pinned: json['pinned'] ?? false,
      tags: json['tags'] ?? '',
      serverType: json['server_type'] ?? '',
      serverTypeDisplay: json['server_type_display'] ?? '',
      ipAddress: json['ip_address'],
      port: json['port'],
      lastStatus: json['last_status'] ?? 'UNKNOWN',
      lastStatusDisplay: json['last_status_display'] ?? 'Unknown',
      lastHttpOk: json['last_http_ok'],
      cpuPercent: _toDouble(json['last_cpu_percent']),
      ramPercent: _toDouble(json['last_ram_percent']),
      latencyMs: json['last_latency_ms'],
      lastChecked: json['last_checked'] != null ? DateTime.parse(json['last_checked']) : null,
      watchDirectory: json['watch_directory'],
      latestFolderName: json['latest_folder_name'],
      latestFolderFiles: json['latest_folder_files'],
      latestFolderSizeMb: json['latest_folder_size_mb'],
      latestFolderCreated: json['latest_folder_created'] != null ? DateTime.parse(json['latest_folder_created']) : null,
    );
  }

  static double? _toDouble(dynamic value) {
    if (value == null) return null;
    if (value is int) return value.toDouble();
    if (value is double) return value;
    return null;
  }
}
