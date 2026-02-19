# Specification: Dashboard Metrics & Agent Integration

## 1. Overview
This track addresses several UI/UX issues on the dashboard and deepens the integration of the Python monitoring agents. The goal is to ensure server metrics are accurate (agent-sourced), real-time (WebSocket-driven), and visually complete (fixing the trend chart and UI artifacts).

## 2. Functional Requirements

### 2.1 UI Cleanup
- **Remove Code Artifact:** Locate and remove the stray JavaScript function `closePanel()` appearing as plain text at the bottom left of the dashboard.

### 2.2 Agent-Based Metrics Integration
- **Source Transition:** Update the server metrics display logic to prioritize data collected via the Python agents (`agent_metrics` or equivalent) over legacy polling methods.
- **Agent Deployment Support:** Ensure the dashboard/backend correctly handles data ingestion from distributed agents as the primary source for CPU, RAM, and Load.

### 2.3 "Performance Trend" Chart Fix
- **Investigation:** Determine why the "Performance Trend" chart is currently empty (gridlines only).
- **Data Rendering:** Fix the chart logic (ApexCharts) to display historical trends for:
    - CPU & RAM usage.
    - Network Throughput (In/Out).
    - Latency (Ping/HTTP response time).
- **Data Source Verification:** If data is missing from the database, implement/fix the aggregation logic required to feed this chart.

### 2.4 Real-time Updates (WebSockets)
- **Automatic Refresh:** Implement a 30-second update interval for server metrics.
- **Technology:** Use **Django Channels** to push updates from the server to the client.
- **Behavior:** The dashboard should update metrics dynamically without a full page refresh.

## 3. Non-Functional Requirements
- **Performance:** WebSocket messages should be lightweight to maintain high-density dashboard performance.
- **Maintainability:** Follow existing Django Channels patterns and ApexCharts configurations.

## 4. Acceptance Criteria
- [ ] No stray text `function closePanel() ...` is visible on any dashboard page.
- [ ] Server metrics update automatically every 30 seconds via WebSockets.
- [ ] The "Performance Trend" chart displays meaningful historical data for CPU, RAM, Network, and Latency.
- [ ] Metrics displayed on the dashboard are verified to be coming from the agent-sourced data.

## 5. Out of Scope
- Modifications to the React Native mobile application.
- Implementation of new alerting or notification rules.
- Redesign of the "NOC-style" grid layout itself.
