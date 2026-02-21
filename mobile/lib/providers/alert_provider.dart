import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../models/alert.dart';
import 'dashboard_provider.dart';

final alertsProvider = FutureProvider<List<Alert>>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final response = await client.dio.get('/mobile/alerts/');
  
  final List<dynamic> data = response.data['alerts'];
  return data.map((a) => Alert.fromJson(a)).toList();
});
