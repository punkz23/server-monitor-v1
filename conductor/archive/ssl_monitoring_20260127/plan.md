# Implementation Plan: SSL Certificate Monitoring

This plan outlines the steps to implement automatic SSL certificate discovery, parsing, and dashboard display, adhering to the project's TDD and lightweight agent principles.

## Phase 1: Agent-Side Collection Logic [checkpoint: 25083d0]
- [x] Task: Implement SSL certificate discovery and parsing in the agent script. 7acf63e
    - [x] Create a unit test for certificate parsing using dummy PEM data.
    - [x] Implement `get_ssl_metrics(paths)` in the agent script using only the `ssl` and `datetime` standard libraries.
    - [x] Add logic to scan standard paths (e.g., `/etc/letsencrypt/live`) for `.pem` or `.crt` files.
    - [x] Integrate `get_ssl_metrics` into the main `get_system_metrics` collection loop.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Agent-Side Collection Logic' (Protocol in workflow.md)

## Phase 2: Backend Ingestion and Storage
- [x] Task: Update the backend to ingest and store SSL metadata. 40e3ffa
    - [x] Create a migration to add an `ssl_metrics` JSONField to the `ServerMetrics` (or `Server`) model.
    - [x] Update the `agent_metrics` ingestion view in `monitor/agent_views.py` to process the incoming SSL data.
    - [x] Update `MetricsMonitorService` to format SSL data for the frontend, including "worst-case" status calculation.
    - [x] Write integration tests verifying that a POST request with SSL data is correctly saved and formatted.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Backend Ingestion and Storage' (Protocol in workflow.md)
    -   *Verified:* Migrations applied, ingestion view updated, service formatting implemented, and integration tests passed.

## Phase 3: Dashboard UI Integration [checkpoint: 9b708b1]
- [x] Task: Add SSL status indicators to the main dashboard. f6a8688
    - [x] Update the server card template in `dashboard_new.html` to include a compact SSL badge.
    - [x] Implement color-coding logic for the badge based on days remaining (Green > 30, Orange < 30, Red < 7).
    - [x] Update the server side-panel JS logic to render the full list of discovered certificates when a server is clicked.
    - [x] Verify responsive layout on mobile screens.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Dashboard UI Integration' (Protocol in workflow.md)

## Phase 4: End-to-End Verification and Deployment [checkpoint: 0f10519]
- [x] Task: Deploy and verify the feature on the Dummy server.
    - [x] Update `auto_deploy_agents.py` to include the new agent logic in the embedded script.
    - [x] Redeploy the agent to the 'Dummy' server.
    - [x] Manually verify that SSL certificates are discovered and displayed on the dashboard.
- [x] Task: Conductor - User Manual Verification 'Phase 4: End-to-End Verification and Deployment' (Protocol in workflow.md)
