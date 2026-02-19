# Initial Concept

The project's goal is to monitor server health, network status, and infrastructure components, providing a comprehensive web dashboard and mobile interface.

### Key Features

- **Robust Server Monitoring**: Real-time collection of CPU, RAM, Load, Network, and Database metrics via portable, dependency-free Python agents.

- **Intelligent Alerting**: Multi-channel notification system (Email, Console) with support for dependency-based alert suppression (e.g., suppressing secondary alerts when a server is down).

- **Real-time Dashboard**: Modern, high-density "NOC-style" web interface with interactive historical charts, categorization, and customizable grid layouts.

- **Reliable Health Checks**: Support for HTTP/HTTPS status monitoring with configurable SSL verification skipping for internal/self-signed environments.

- **Secure Data Ingestion**: Validated API endpoints for agent data with bearer token authentication and reliable server identification.

- **Infrastructure Visibility**: Integrated side panel for detailed server health, including SSL certificate tracking, service-level status, and custom directory monitoring.

- **Flexible Deployment**: Support for both system-wide (sudo) and user-space agent installation using systemd (system/user modes) for maximum environment compatibility.
