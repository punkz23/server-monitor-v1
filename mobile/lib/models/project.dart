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
}

class Project {
  final int id;
  final String name;
  final String repoUrl;
  final List<Server> servers;
  final DateTime createdAt;
  final DateTime updatedAt;

  Project({
    required this.id,
    required this.name,
    required this.repoUrl,
    required this.servers,
    required this.createdAt,
    required this.updatedAt,
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
    );
  }
}
