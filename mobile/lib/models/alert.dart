class Alert {
  final int id;
  final String serverName;
  final String title;
  final String message;
  final String severity;
  final String kind;
  final double? value;
  final bool isRecovery;
  final DateTime createdAt;

  Alert({
    required this.id,
    required this.serverName,
    required this.title,
    required this.message,
    required this.severity,
    required this.kind,
    this.value,
    required this.isRecovery,
    required this.createdAt,
  });

  factory Alert.fromJson(Map<String, dynamic> json) {
    return Alert(
      id: json['id'],
      serverName: json['server_name'] ?? 'System',
      title: json['title'] ?? 'Unknown Alert',
      message: json['message'] ?? '',
      severity: json['severity'] ?? 'INFO',
      kind: json['kind'] ?? '',
      value: (json['value'] as num?)?.toDouble(),
      isRecovery: json['is_recovery'] ?? false,
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
