import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../providers/dashboard_provider.dart';

class TerminalWidget extends ConsumerStatefulWidget {
  const TerminalWidget({super.key});

  @override
  ConsumerState<TerminalWidget> createState() => _TerminalWidgetState();
}

class _TerminalWidgetState extends ConsumerState<TerminalWidget> {
  WebSocketChannel? _channel;
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<String> _output = [];
  bool _isConnected = false;
  String? _lastError;

  @override
  void initState() {
    super.initState();
    // Add initial status message
    setState(() {
      _output.add('Terminal initializing...');
    });
    _connect();
  }

  Future<void> _connect() async {
    final client = ref.read(apiClientProvider).value;
    if (client == null) {
      print('Terminal: API client is null');
      setState(() {
        _isConnected = false;
        _lastError = 'API client not available';
        _output.add('Mock terminal mode - API client not available');
        _output.add('This is a simulated terminal for demonstration.');
      });
      return;
    }

    final token = await client.getToken();
    if (token == null) {
      print('Terminal: No authentication token available');
      setState(() {
        _isConnected = false;
        _lastError = 'No authentication token';
        _output.add('Mock terminal mode - No authentication token');
        _output.add('This is a simulated terminal for demonstration.');
      });
      return;
    }

    final uri = Uri.parse(client.baseUrl);
    final wsProtocol = uri.scheme == 'https' ? 'wss' : 'ws';
    
    // Remove /api from baseUrl if present for WS
    String wsBase = client.baseUrl.replaceFirst('/api', '');
    
    // Ensure proper protocol replacement
    if (wsBase.startsWith('http://')) {
      wsBase = wsBase.replaceFirst('http://', 'ws://');
    } else if (wsBase.startsWith('https://')) {
      wsBase = wsBase.replaceFirst('https://', 'wss://');
    }
    
    final wsUrl = '$wsBase/ws/terminal/?token=$token';
    
    print('Terminal: Attempting to connect to: $wsUrl');
    print('Terminal: Base URL: ${client.baseUrl}');
    print('Terminal: Token: ${token.length > 0 ? "Present" : "Missing"}');

    try {
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _channel!.stream.listen(
        (message) {
          print('Terminal: Received message: $message');
          try {
            final data = jsonDecode(message);
            if (data['type'] == 'stdout') {
              setState(() {
                _output.add(data['data']);
              });
              _scrollToBottom();
            } else if (data['type'] == 'error') {
              setState(() {
                _output.add('Error: ${data['message']}');
              });
              _scrollToBottom();
            }
          } catch (e) {
            print('Terminal: Failed to parse message: $e');
            setState(() {
              _output.add('Raw message: $message');
            });
            _scrollToBottom();
          }
        },
        onDone: () {
          print('Terminal: WebSocket connection closed');
          setState(() {
            _isConnected = false;
            _lastError = 'Connection closed';
          });
        },
        onError: (e) {
          print('Terminal: WebSocket error: $e');
          setState(() {
            _isConnected = false;
            _lastError = e.toString();
            _output.add('Connection error: $e');
          });
        },
      );
      setState(() {
        _isConnected = true;
        _lastError = null;
      });
      print('Terminal: Connected successfully');
    } catch (e) {
      print('Terminal: Failed to connect: $e');
      setState(() {
        _isConnected = false;
        _lastError = e.toString();
        _output.add('Failed to connect: $e');
      });
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 100),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _sendCommand() {
    if (_channel != null && _controller.text.isNotEmpty && _isConnected) {
      final command = _controller.text;
      print('Terminal: Sending command: $command');
      _channel!.sink.add(jsonEncode({
        'type': 'stdin',
        'data': command,
      }));
      _controller.clear();
    } else if (!_isConnected) {
      // Mock terminal responses for demonstration
      final command = _controller.text.toLowerCase().trim();
      setState(() {
        _output.add('\$ $command');
        
        if (command.contains('help') || command == '?') {
          _output.add('Available commands:');
          _output.add('  help     - Show this help message');
          _output.add('  ls       - List directory contents');
          _output.add('  pwd      - Show current directory');
          _output.add('  whoami   - Show current user');
          _output.add('  date     - Show current date and time');
          _output.add('  status   - Show server status');
        } else if (command.contains('ls')) {
          _output.add('Documents/  Downloads/  Pictures/  Videos/');
          _output.add('server.log  config.json  backup.sql');
        } else if (command.contains('pwd')) {
          _output.add('/home/dummy-server');
        } else if (command.contains('whoami')) {
          _output.add('dummy-user');
        } else if (command.contains('date')) {
          _output.add(DateTime.now().toString());
        } else if (command.contains('status')) {
          _output.add('Server Status: Online');
          _output.add('CPU Usage: 15%');
          _output.add('Memory Usage: 42%');
          _output.add('Disk Usage: 67%');
        } else if (command.isNotEmpty) {
          _output.add('Command not found: $command');
          _output.add('Type "help" for available commands');
        }
      });
      _controller.clear();
      _scrollToBottom();
    }
  }

  @override
  void dispose() {
    _channel?.sink.close();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          _isConnected ? 'Remote Terminal (Dummy Server)' : 'Terminal (Demo Mode)',
          style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
        ),
        if (!_isConnected)
          const Padding(
            padding: EdgeInsets.only(top: 4.0),
            child: Text(
              'Simulated terminal for demonstration',
              style: TextStyle(color: Colors.grey, fontSize: 12),
            ),
          ),
        const SizedBox(height: 12),
        Container(
          height: 300,
          decoration: BoxDecoration(
            color: Colors.black,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white10),
          ),
          child: Column(
            children: [
              Expanded(
                child: ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(8),
                  itemCount: _output.length,
                  itemBuilder: (context, index) {
                    return Text(
                      _output[index],
                      style: const TextStyle(
                        color: Colors.lightGreenAccent,
                        fontFamily: 'monospace',
                        fontSize: 12,
                      ),
                    );
                  },
                ),
              ),
              if (!_isConnected)
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            _lastError != null ? Icons.error_outline : Icons.warning_outlined,
                            color: _lastError != null ? Colors.red : Colors.orange,
                            size: 16,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _lastError != null ? 'Connection Failed' : 'Disconnected',
                            style: TextStyle(
                              color: _lastError != null ? Colors.red : Colors.orange,
                              fontSize: 12,
                            ),
                          ),
                          const Spacer(),
                          TextButton(
                            onPressed: () {
                              setState(() {
                                _lastError = null;
                                _output.clear();
                              });
                              _connect();
                            },
                            child: const Text('Reconnect'),
                          ),
                        ],
                      ),
                      if (_lastError != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          'Last error: $_lastError',
                          style: const TextStyle(color: Colors.redAccent, fontSize: 10),
                        ),
                      ],
                    ],
                  ),
                ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                decoration: const BoxDecoration(
                  border: Border(top: BorderSide(color: Colors.white10)),
                ),
                child: Row(
                  children: [
                    const Text('\$', style: TextStyle(color: Colors.white70)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: _controller,
                        style: const TextStyle(color: Colors.white, fontFamily: 'monospace', fontSize: 14),
                        decoration: const InputDecoration(
                          border: InputBorder.none,
                          hintText: 'Enter command...',
                          hintStyle: TextStyle(color: Colors.white24, fontSize: 14),
                        ),
                        onSubmitted: (_) => _sendCommand(),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.send, color: Colors.blue, size: 20),
                      onPressed: _sendCommand,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
