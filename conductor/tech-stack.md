# Tech Stack

## Programming Languages
- **Python:** Primary language for the backend, agent scripts, and server-side logic.
- **JavaScript/TypeScript:** Used for the mobile application development with React Native.

## Frameworks
- **Django:** Web framework for the backend, handling web dashboard, APIs, and overall server logic.
- **Django Channels:** For real-time WebSocket communication.
- **ApexCharts:** Primary library for modern, interactive time-series data visualizations.
- **React Native:** Mobile application framework for building the cross-platform iOS and Android apps.

## Database
- **SQLite:** (Likely) Used for local development and potentially smaller deployments due to the presence of `db.sqlite3`.
- **PyMySQL:** Python driver for MySQL, indicating potential use of MySQL for larger deployments or specific components.

## Architecture
The project follows a multi-component architecture:
- **Django Backend:** Provides the core server functionalities, web interface, and APIs.
- **React Native Mobile App:** Client application for iOS and Android, interacting with the backend APIs.
- **Python Agents:** Lightweight, zero-dependency scripts (standard library only) designed for maximum compatibility across Linux distributions without requiring pip or virtual environments.
- **Notification Service:** Extensible multi-channel alert delivery system.