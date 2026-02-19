import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../models/ssl_certificate.dart';
import 'dashboard_provider.dart';

final sslCertificatesProvider = FutureProvider<List<SslCertificate>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final response = await client.dio.get('/certificates/');
  
  final List<dynamic> data = response.data;
  return data.map((s) => SslCertificate.fromJson(s)).toList();
});
