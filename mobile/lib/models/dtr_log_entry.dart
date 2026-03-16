class DtrLogEntry {
  final String id;
  final String userName;
  final String userId;
  final String type; // 'IN' or 'OUT'
  final DateTime timestamp;
  final String? locationName;
  final double? latitude;
  final double? longitude;
  final double? confidenceScore;
  final String? deviceName;
  final bool isLate;
  final String? reason;

  DtrLogEntry({
    required this.id,
    required this.userName,
    required this.userId,
    required this.type,
    required this.timestamp,
    this.locationName,
    this.latitude,
    this.longitude,
    this.confidenceScore,
    this.deviceName,
    this.isLate = false,
    this.reason,
  });

  factory DtrLogEntry.fromJson(Map<String, dynamic> json) {
    return DtrLogEntry(
      id: json['id']?.toString() ?? '',
      userName: json['user_name'] ?? json['name'] ?? 'Unknown',
      userId: json['user_id']?.toString() ?? json['contact_id']?.toString() ?? '',
      type: json['type'] ?? 'IN',
      timestamp: DateTime.parse(json['timestamp'] ?? DateTime.now().toIso8601String()),
      locationName: json['location_name'],
      latitude: json['latitude']?.toDouble(),
      longitude: json['longitude']?.toDouble(),
      confidenceScore: json['confidence_score']?.toDouble(),
      deviceName: json['device_name'],
      isLate: json['is_late'] ?? false,
      reason: json['reason'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_name': userName,
      'user_id': userId,
      'type': type,
      'timestamp': timestamp.toIso8601String(),
      'location_name': locationName,
      'latitude': latitude,
      'longitude': longitude,
      'confidence_score': confidenceScore,
      'device_name': deviceName,
      'is_late': isLate,
      'reason': reason,
    };
  }
}
