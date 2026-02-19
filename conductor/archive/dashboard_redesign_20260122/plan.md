# Implementation Plan: Dashboard Redesign & Metrics Enhancement

## Phase 1: Frontend Infrastructure & Layout [checkpoint: 5267b91]
- [x] Task: Set up ApexCharts and necessary frontend dependencies in the Django project. a02580b
- [x] Task: Create the base HTML/CSS structure for the hybrid grid layout (NOC-style with categories). 555125d
- [x] Task: Implement the Side Panel (Drawer) component for server details. 341ca25
- [x] Task: Conductor - User Manual Verification 'Phase 1: Frontend Infrastructure & Layout' (Protocol in workflow.md)

## Phase 2: Core Dashboard Data & Grid Implementation [checkpoint: 47c730e]
- [x] Task: Write Tests: Verify dashboard view returns server data grouped by category. e18ac5f
- [x] Task: Implement: Update the main dashboard view to fetch and group servers by type. e18ac5f
- [x] Task: Implement: Create the responsive server card component with real-time status and core metrics. 341ca25
- [x] Task: Implement: Integrate CSS for mobile responsiveness of the grid. 0fd4275
- [x] Task: Conductor - User Manual Verification 'Phase 2: Core Dashboard Data & Grid Implementation' (Protocol in workflow.md)

## Phase 3: Side Panel Metrics & Visualizations [checkpoint: 10cc761]
- [x] Task: Write Tests: Verify API endpoint for detailed server metrics (Historical, SSL, Directory Watch). a7747fc
- [x] Task: Implement: Backend logic for detailed metric retrieval including SSL status and directory monitoring. 628415f
- [x] Task: Implement: Create ApexCharts components for CPU, RAM, and Disk historical trends. 628415f
- [x] Task: Implement: Side panel sections for SSL Certificates, Service Status, and Directory Watch. 628415f
- [x] Task: Implement: Sidebar/Header for Global Summary and Alert History access. 10cc761
- [x] Task: Conductor - User Manual Verification 'Phase 3: Side Panel Metrics & Visualizations' (Protocol in workflow.md)

## Phase 4: Optimization & Final Polish
- [x] Task: Write Tests: Performance benchmarks for dashboard load time. c1715f0
- [x] Task: Implement: Optimize data fetching and implement caching/WebSocket updates to meet <200ms target. a7747fc
- [x] Task: Implement: Final visual styling (dark mode, typography, iconography). 10cc761
- [x] Task: Conductor - User Manual Verification 'Phase 4: Optimization & Final Polish' (Protocol in workflow.md)

## Phase 5: UI Enhancements & Fixes [checkpoint: 89f777d]
- [x] Task: Implement: Grid column count toggle (2, 3, 4, 6 columns). e42f80f
- [x] Task: Implement: Directory Watch CRUD (Add, Edit, Delete buttons). e42f80f
- [x] Task: Implement: Fix Performance Trends charts to display historical data correctly. e42f80f
- [x] Task: Conductor - User Manual Verification 'Phase 5: UI Enhancements & Fixes' (Protocol in workflow.md)
