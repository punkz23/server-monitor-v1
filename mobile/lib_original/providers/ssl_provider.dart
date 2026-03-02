import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/ssl_certificate.dart';
import 'dashboard_provider.dart';

final sslCertificatesProvider = FutureProvider<List<SslCertificate>>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final response = await client.dio.get('/certificates/');
  
  // DRF with pagination returns a map with a 'results' key containing the list
  final List<dynamic> data = response.data is Map ? response.data['results'] : response.data;
  return data.map((s) => SslCertificate.fromJson(s)).toList();
});
