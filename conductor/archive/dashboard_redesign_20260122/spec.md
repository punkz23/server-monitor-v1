# Specification: Dashboard Redesign & Metrics Enhancement

## 1. Overview
The goal of this track is to completely redesign the Django web dashboard to provide a modern, high-performance, and mobile-responsive "NOC-style" monitoring interface. This includes a visual overhaul, UX improvements (side panel details), and the integration of new historical and service-level metrics using ApexCharts.

## 2. Functional Requirements

### 2.1 Hybrid Grid Layout
- Implement a high-density grid of server status cards.
- Organize cards into categories (e.g., Web, Database, Storage) with quick-navigation tabs or a sidebar.
- Each card must display real-time status (UP/DOWN) and core metrics (CPU, RAM, Disk usage percentages).
- **Column Toggle:** Include a UI control to toggle between different grid densities (e.g., 2, 3, 4, or 6 columns).

### 2.2 Server Detail Side Panel (Drawer)
- Clicking a card opens a side panel from the right.
- **Service Status:** Display the status of key services (Web Server, DB) on that specific node.
- **SSL Certificates:** For web servers, display certificate validity, issuer, and days until expiration.
- **Directory Watch:** 
    - Display status and recent changes for monitored custom directories.
    - **CRUD Management:** Allow users to Add, Edit, and Delete directory paths directly from the side panel.
- **Historical Trends:** 
    - Interactive time-series charts using **ApexCharts** for CPU, RAM, and Disk usage (e.g., last 24 hours).
    - **Fix:** Ensure charts correctly render and animate historical data points retrieved from the API.
- **Network Stats:** Real-time upload/download speeds and total bandwidth usage.
- **Storage Details:** Partition-level usage and I/O performance metrics.

### 2.3 System-Wide Metrics
- **Alert History:** A global, searchable log of recent system alerts and events accessible from the main dashboard.
- **Global Summary:** A persistent header showing overall infrastructure health.

## 3. Non-Functional Requirements
- **Performance:** Optimize data fetching to ensure the dashboard loads in under 200ms. Use background updates/WebSockets for real-time changes.
- **Mobile Responsiveness:** The layout must be fully responsive, ensuring cards and side panels are usable on smartphones and tablets.
- **Visual Design:** Modernize typography, colors (e.g., dark mode support), and iconography.

## 4. Acceptance Criteria
- [ ] Dashboard displays all servers in a categorized grid layout.
- [ ] Side panel opens correctly with detailed metrics, SSL info, and directory changes.
- [ ] ApexCharts visualize historical data accurately.
- [ ] Dashboard is fully functional and visually coherent on mobile browsers.
- [ ] Global alert history is viewable and searchable.
- [ ] Page load performance meets the <200ms target (excluding async data loads).

## 5. Out of Scope
- Redesigning the mobile application (React Native) UI (this track focuses on the Django Web Dashboard).
