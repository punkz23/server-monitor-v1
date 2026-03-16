import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/dtr_model.dart';
import 'dashboard_provider.dart';

final dtrAccuracyProvider = FutureProvider<DtrAccuracyData>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final r = await client.dio.get('/dtr/accuracy-friction/');
  return DtrAccuracyData.fromJson(r.data['data']);
});

final dtrPerformanceProvider = FutureProvider<DtrPerformanceData>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final r = await client.dio.get('/dtr/performance-latency/');
  return DtrPerformanceData.fromJson(r.data['data']);
});

final dtrEnvironmentalProvider =
    FutureProvider<DtrEnvironmentalData>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final r = await client.dio.get('/dtr/environmental-hardware/');
  return DtrEnvironmentalData.fromJson(r.data['data']);
});

final dtrOperationalProvider =
    FutureProvider<DtrOperationalData>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final r = await client.dio.get('/dtr/operational-security/');
  return DtrOperationalData.fromJson(r.data['data']);
});

final dtrHeatmapProvider =
    FutureProvider<List<DtrHeatmapLocation>>((ref) async {
  final client = ref.watch(apiClientProvider).value!;
  final r = await client.dio.get('/dtr/heatmap/');
  final list = r.data['data'] as List<dynamic>? ?? [];
  return list.map((e) => DtrHeatmapLocation.fromJson(e)).toList();
});
