import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../models/dashboard_summary.dart';

final apiClientProvider = Provider((ref) => ApiClient());

final dashboardSummaryProvider = FutureProvider<DashboardSummary>((ref) async {
  final client = ref.watch(apiClientProvider);
  final response = await client.dio.get('/mobile/dashboard/');
  return DashboardSummary.fromJson(response.data);
});
