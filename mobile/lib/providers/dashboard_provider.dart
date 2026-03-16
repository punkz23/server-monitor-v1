import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../models/dashboard_summary.dart';

final apiClientProvider = AsyncNotifierProvider<ApiClientNotifier, ApiClient>(
  () => ApiClientNotifier(),
);

class ApiClientNotifier extends AsyncNotifier<ApiClient> {
  @override
  Future<ApiClient> build() async {
    return await ApiClient.create();
  }

  Future<void> setBaseUrl(String newUrl) async {
    final apiClient = await future;
    await apiClient.setBaseUrl(newUrl);
    state = AsyncValue.data(apiClient);
  }
}


final dashboardSummaryProvider = FutureProvider<DashboardSummary>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final response = await client.dio.get('mobile/dashboard/');
  return DashboardSummary.fromJson(response.data);
});
