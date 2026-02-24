import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/network_device.dart';
import 'dashboard_provider.dart';

final networkDevicesProvider = FutureProvider<List<NetworkDevice>>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final response = await client.dio.get('/mobile/network-devices/');
  
  final List<dynamic> data = response.data['devices'];
  return data.map((d) => NetworkDevice.fromJson(d)).toList();
});

class NetworkScanNotifier extends StateNotifier<AsyncValue<int>> {
  final Ref ref;
  NetworkScanNotifier(this.ref) : super(const AsyncValue.data(0));

  Future<void> triggerScan() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider).value!;
      final response = await client.dio.post('/mobile/network-devices/scan/');
      
      final int count = response.data['count'] ?? 0;
      
      // Refresh the list after successful scan
      ref.invalidate(networkDevicesProvider);
      
      state = AsyncValue.data(count);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }
}

final networkScanProvider = StateNotifierProvider<NetworkScanNotifier, AsyncValue<int>>((ref) {
  return NetworkScanNotifier(ref);
});
