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

  Future<bool> triggerScan() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider).value!;
      await client.dio.post('/mobile/network-devices/scan/');
      
      state = const AsyncValue.data(null);
      
      // We don't wait 5s here anymore, we'll let the UI handle the immediate feedback
      // and the user can refresh later or we can do a background refresh.
      // But for now, returning true so UI can show snackbar.
      
      // Auto-refresh once after 5s anyway
      _backgroundRefresh(5);
      
      return true;
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
      return false;
    }
  }

  void _backgroundRefresh(int seconds) async {
    await Future.delayed(Duration(seconds: seconds));
    ref.invalidate(networkDevicesProvider);
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

  Future<bool> clearDevices() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider).value!;
      await client.dio.post('/mobile/network-devices/clear/');
      
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
