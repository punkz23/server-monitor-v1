import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/server.dart';
import '../models/server_detail.dart';
import 'dashboard_provider.dart';

final serversProvider = FutureProvider<List<Server>>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final response = await client.dio.get('mobile/server-status/');
  
  final List<dynamic> data = response.data['servers'];
  return data.map((s) => Server.fromJson(s)).toList();
});

final serverDetailProvider = FutureProvider.family<ServerDetail, int>((ref, serverId) async {
  final client = ref.watch(apiClientProvider).value!;
  // Use the detailed metrics API we optimized earlier
  final response = await client.dio.get('v2/metrics/server/$serverId/detailed/');
  return ServerDetail.fromJson(response.data);
});
