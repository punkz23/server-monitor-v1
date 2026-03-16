import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/network_device_provider.dart';
import '../models/network_device.dart';

class NetworkDevicesScreen extends ConsumerWidget {
  const NetworkDevicesScreen({super.key});

  IconData _getDeviceIcon(String type) {
    switch (type.toUpperCase()) {
      case 'FIREWALL':
        return Icons.security;
      case 'SWITCH':
        return Icons.settings_input_component;
      case 'ROUTER':
        return Icons.router;
      case 'PC':
        return Icons.computer;
      case 'MOBILE':
        return Icons.smartphone;
      case 'PRINTER':
        return Icons.print;
      case 'NAS':
        return Icons.storage;
      case 'ACCESS_POINT':
        return Icons.wifi;
      default:
        return Icons.devices_other;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final devicesAsync = ref.watch(networkDevicesProvider);
    final actionState = ref.watch(networkDeviceActionProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0F0F23),
      appBar: AppBar(
        title: const Text('Network Devices'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.add_circle_outline, color: Colors.blue),
            onPressed: () => _showAddDeviceDialog(context, ref),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(networkDevicesProvider),
          ),
        ],
      ),
      body: Column(
        children: [
          devicesAsync.when(
            data: (devices) => _buildScanHeader(context, ref, actionState, devices.length),
            loading: () => _buildScanHeader(context, ref, actionState, 0),
            error: (_, __) => _buildScanHeader(context, ref, actionState, 0),
          ),
          Expanded(
            child: devicesAsync.when(
              data: (devices) => _buildDeviceList(context, ref, devices),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, _) => Center(
                child: Text('Error: $err', style: const TextStyle(color: Colors.white70)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showAddDeviceDialog(BuildContext context, WidgetRef ref) {
    final nameController = TextEditingController();
    final ipController = TextEditingController();
    String selectedType = 'UNKNOWN';

    final types = [
      'UNKNOWN', 'FIREWALL', 'SWITCH', 'ROUTER', 'PC', 'MOBILE', 'PRINTER', 'NAS', 'ACCESS_POINT'
    ];

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          backgroundColor: const Color(0xFF181929),
          title: const Text('Add Network Device', style: TextStyle(color: Colors.white)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameController,
                  style: const TextStyle(color: Colors.white),
                  decoration: _inputDecoration('Device Name', Icons.label),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: ipController,
                  style: const TextStyle(color: Colors.white),
                  decoration: _inputDecoration('IP Address', Icons.network_check),
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: selectedType,
                  dropdownColor: const Color(0xFF181929),
                  style: const TextStyle(color: Colors.white),
                  decoration: _inputDecoration('Device Type', Icons.category),
                  items: types.map((t) => DropdownMenuItem(
                    value: t,
                    child: Text(t),
                  )).toList(),
                  onChanged: (val) => setState(() => selectedType = val!),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel', style: TextStyle(color: Colors.white38)),
            ),
            ElevatedButton(
              onPressed: () async {
                if (nameController.text.isEmpty || ipController.text.isEmpty) return;
                
                final success = await ref.read(networkDeviceActionProvider.notifier).addDevice(
                  nameController.text,
                  ipController.text,
                  selectedType,
                );

                if (success && context.mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Device added successfully')),
                  );
                }
              },
              style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
              child: const Text('Add Device', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String label, IconData icon) {
    return InputDecoration(
      labelText: label,
      labelStyle: const TextStyle(color: Colors.white38, fontSize: 12),
      prefixIcon: Icon(icon, color: Colors.white38, size: 20),
      filled: true,
      fillColor: const Color(0xFF0F0F23),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Colors.blue)),
    );
  }

  Widget _buildScanHeader(BuildContext context, WidgetRef ref, AsyncValue<dynamic> actionState, int count) {
    final isScanning = actionState is AsyncLoading;

    return Container(
      padding: const EdgeInsets.all(16),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF181929),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.blue.withOpacity(0.1)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Network Discovery ($count devices)',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                    ),
                    const Text(
                      'Target: 192.168.253.0/24',
                      style: TextStyle(color: Colors.white38, fontSize: 12),
                    ),
                  ],
                ),
              ),
              ElevatedButton.icon(
                onPressed: isScanning ? null : () async {
                  final success = await ref.read(networkDeviceActionProvider.notifier).triggerScan();
                  if (success && context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Server-side scan initiated for 192.168.253.0/24.'),
                        duration: Duration(seconds: 3),
                      ),
                    );
                  }
                },
                icon: isScanning
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.search, size: 18),
                label: Text(isScanning ? 'Scanning...' : 'Scan Now'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                  disabledBackgroundColor: Colors.blue.withOpacity(0.3),
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            ],
          ),
          if (count > 0) ...[
            const SizedBox(height: 8),
            const Divider(color: Colors.white10),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton.icon(
                  onPressed: isScanning ? null : () => _showClearConfirm(context, ref),
                  icon: const Icon(Icons.delete_sweep_outlined, size: 18, color: Colors.redAccent),
                  label: const Text('Clear All', style: TextStyle(color: Colors.redAccent, fontSize: 12)),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  void _showClearConfirm(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF181929),
        title: const Text('Clear List?', style: TextStyle(color: Colors.white)),
        content: const Text('This will remove all discovered devices from the database.', style: TextStyle(color: Colors.white70)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              ref.read(networkDeviceActionProvider.notifier).clearDevices();
              Navigator.pop(context);
            },
            child: const Text('Clear All', style: TextStyle(color: Colors.redAccent)),
          ),
        ],
      ),
    );
  }

  Widget _buildDeviceList(BuildContext context, WidgetRef ref, List<NetworkDevice> devices) {
    if (devices.isEmpty) {
      return const Center(
        child: Text('No devices found. Run a scan to discover devices.', 
            style: TextStyle(color: Colors.white24)),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: devices.length,
      itemBuilder: (context, index) {
        final device = devices[index];
        return _buildDeviceCard(context, ref, device);
      },
    );
  }

  Widget _buildDeviceCard(BuildContext context, WidgetRef ref, NetworkDevice device) {
    final bool isMonitored = (device as dynamic).enabled ?? false; // Need to ensure model has it or cast to dynamic

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF181929),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isMonitored 
              ? Colors.blue.withOpacity(0.3)
              : (device.isActive ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1)),
        ),
      ),
      child: Column(
        children: [
          ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: (device.isActive ? Colors.green : Colors.grey).withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                _getDeviceIcon(device.deviceType),
                color: device.isActive ? Colors.green : Colors.grey,
                size: 24,
              ),
            ),
            title: Text(
              device.name,
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text(
                  '${device.ipAddress} • ${device.deviceTypeDisplay}',
                  style: const TextStyle(color: Colors.white38, fontSize: 12),
                ),
                if (device.macAddress != null)
                  Text(
                    device.macAddress!,
                    style: const TextStyle(color: Colors.white24, fontSize: 10, fontFamily: 'monospace'),
                  ),
              ],
            ),
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: (device.isActive ? Colors.green : Colors.red).withOpacity(0.1),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                device.isActive ? 'UP' : 'DOWN',
                style: TextStyle(
                  color: device.isActive ? Colors.green : Colors.red,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          if (!isMonitored)
            Padding(
              padding: const EdgeInsets.only(left: 16, right: 16, bottom: 12),
              child: SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () async {
                    final success = await ref.read(networkDeviceActionProvider.notifier).addDevice(
                      device.name,
                      device.ipAddress,
                      device.deviceType,
                    );
                    if (success && context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('${device.name} saved for monitoring')),
                      );
                    }
                  },
                  icon: const Icon(Icons.add_moderator, size: 16),
                  label: const Text('Save for Monitoring', style: TextStyle(fontSize: 12)),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.blue,
                    side: const BorderSide(color: Colors.blue),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
              ),
            )
          else
            const Padding(
              padding: EdgeInsets.only(bottom: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.check_circle, size: 12, color: Colors.blue),
                  SizedBox(width: 4),
                  Text('Currently Monitored', style: TextStyle(color: Colors.blue, fontSize: 10)),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
