class NetworkDevice {
  final int id;
  final String name;
  final String deviceType;
  final String deviceTypeDisplay;
  final String ipAddress;
  final String? macAddress;
  final String vendor;
  final String? hostname;
  final bool isActive;
  final DateTime? lastSeen;
  final bool enabled;

  NetworkDevice({
    required this.id,
    required this.name,
    required this.deviceType,
    required this.deviceTypeDisplay,
    required this.ipAddress,
    this.macAddress,
    required this.vendor,
    this.hostname,
    required this.isActive,
    this.lastSeen,
    required this.enabled,
  });

  factory NetworkDevice.fromJson(Map<String, dynamic> json) {
    return NetworkDevice(
      id: json['id'],
      name: json['name'] ?? 'Unknown Device',
      deviceType: json['device_type'] ?? 'UNKNOWN',
      deviceTypeDisplay: json['device_type_display'] ?? 'Unknown',
      ipAddress: json['ip_address'] ?? '',
      macAddress: json['mac_address'],
      vendor: json['vendor'] ?? 'Unknown',
      hostname: json['hostname'],
      isActive: json['is_active'] ?? false,
      last_seen: json['last_seen'] != null ? DateTime.parse(json['last_seen']) : null,
      enabled: json['enabled'] ?? false,
    );
  }
}
