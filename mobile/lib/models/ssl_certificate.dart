class SslCertificate {
  final int id;
  final int? serverId;
  final String? serverName;
  final String name;
  final String domain;
  final String? issuer;
  final DateTime? expiresAt;
  final int daysUntilExpiry;
  final bool isValid;
  final DateTime? lastChecked;

  SslCertificate({
    required this.id,
    this.serverId,
    this.serverName,
    required this.name,
    required this.domain,
    this.issuer,
    this.expiresAt,
    required this.daysUntilExpiry,
    required this.isValid,
    this.lastChecked,
  });

  factory SslCertificate.fromJson(Map<String, dynamic> json) {
    return SslCertificate(
      id: json['id'] ?? 0,
      serverId: json['server_id'],
      serverName: json['server_name'],
      name: json['name'] ?? '',
      domain: json['domain'] ?? '',
      issuer: json['issuer'],
      expiresAt: json['expires_at'] != null ? DateTime.parse(json['expires_at']) : null,
      daysUntilExpiry: json['days_until_expiry'] ?? 0,
      isValid: json['is_valid'] ?? false,
      lastChecked: json['last_checked'] != null ? DateTime.parse(json['last_checked']) : null,
    );
  }

  String get status {
    if (!isValid || daysUntilExpiry <= 0) return 'expired';
    if (daysUntilExpiry <= 7) return 'critical';
    if (daysUntilExpiry <= 30) return 'warning';
    return 'good';
  }
}
