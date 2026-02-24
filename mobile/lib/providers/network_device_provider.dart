import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/network_device.dart';
import 'dashboard_provider.dart';

final networkDevicesProvider = FutureProvider<List<NetworkDevice>>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final response = await client.dio.get('/mobile/network-devices/');
  
  final List<dynamic> data = response.data['devices'];
  return data.map((d) => NetworkDevice.fromJson(d)).toList();
});

class NetworkDeviceNotifier extends StateNotifier<AsyncValue<dynamic>> {
  final Ref ref;
  NetworkDeviceNotifier(this.ref) : super(const AsyncValue.data(null));

  Future<void> triggerScan() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider).value!;
      await client.dio.post('/mobile/network-devices/scan/');
      
      // Wait a few seconds for the server-side scan to make some progress
      await Future.delayed(const Duration(seconds: 5));
      
      // Refresh the list
      ref.invalidate(networkDevicesProvider);
      
      state = const AsyncValue.data(null);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  Future<bool> addDevice(String name, String ipAddress, String type) async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider).value!;
      await client.dio.post('/mobile/network-devices/add/', data: {
        'name': name,
        'ip_address': ipAddress,
        'device_type': type,
      });
      
      ref.invalidate(networkDevicesProvider);
      state = const AsyncValue.data(null);
      return true;
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
      return false;
    }
  }
}

final networkDeviceActionProvider = StateNotifierProvider<NetworkDeviceNotifier, AsyncValue<dynamic>>((ref) {
  return NetworkDeviceNotifier(ref);
});
