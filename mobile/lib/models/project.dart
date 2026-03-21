import 'pull_request.dart';

class Server {
  final int id;
  final String hostname;
  final String user;
  final String path;
  final DateTime createdAt;
  final DateTime updatedAt;

  Server({
    required this.id,
    required this.hostname,
    required this.user,
    required this.path,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Server.fromJson(Map<String, dynamic> json) {
    return Server(
      id: json['id'],
      hostname: json['hostname'],
      user: json['user'],
      path: json['path'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'hostname': hostname,
      'user': user,
      'path': path,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

class Project {
  final int id;
  final String name;
  final String repoUrl;
  final List<Server> servers;
  final DateTime createdAt;
  final DateTime updatedAt;
  final ProjectStatus? status; // Optional status information

  Project({
    required this.id,
    required this.name,
    required this.repoUrl,
    required this.servers,
    required this.createdAt,
    required this.updatedAt,
    this.status,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    var serversList = json['servers'] as List;
    List<Server> servers = serversList.map((i) => Server.fromJson(i)).toList();

    return Project(
      id: json['id'],
      name: json['name'],
      repoUrl: json['repo_url'],
      servers: servers,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      status: json['status'] != null ? ProjectStatus.fromJson(json['status']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'repo_url': repoUrl,
      'servers': servers.map((server) => server.toJson()).toList(),
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'status': status?.toJson(),
    };
  }
}
