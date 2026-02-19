# Specification: SSL Certificate Monitoring and Display

## Overview
This feature adds the ability to monitor and display SSL certificate status for web servers directly on the dashboard. The monitoring will be performed by the lightweight Python agents running on the servers, which will automatically discover and parse local certificate files.

## Functional Requirements
- **Automatic Discovery:** The Python agent will automatically scan standard system paths (e.g., `/etc/letsencrypt/live/`, `/etc/ssl/certs/`) to identify SSL certificates.
- **Metadata Collection:** For each discovered certificate, the agent will extract and report:
    - **Common Name (CN):** The primary domain covered by the certificate.
    - **Expiry Date:** The date the certificate expires.
    - **Days Remaining:** Calculated time until expiration.
    - **Issuer Information:** The certificate authority that issued the cert.
- **Dashboard Integration:**
    - Each server card on the main dashboard grid will display a compact SSL status badge.
    - The badge will represent the status of the "worst-case" certificate (the one closest to expiration).
    - Status Colors:
        - **Green:** Certificate is valid and has > 30 days remaining.
        - **Orange:** Certificate expires in < 30 days.
        - **Red:** Certificate is expired or expires in < 7 days.
- **Side Panel Details:** When a server is selected, the side panel will list all discovered certificates with their full details (Issuer, CN, Expiry).

## Non-Functional Requirements
- **Dependency-Free Agent:** The agent-side collection logic must use only the Python standard library (e.g., `ssl` and `datetime` modules) to remain portable.
- **Permissions:** The agent service must have sufficient permissions to read certificate files (often requiring root or membership in a specific group).
- **Efficiency:** Scanning and parsing should be performant and happen at a configurable interval (defaulting to once per hour to minimize I/O).

## Acceptance Criteria
- [ ] Python agent successfully identifies certificates in `/etc/letsencrypt/live/`.
- [ ] Agent correctly parses CN, Expiry, and Issuer using the `ssl` module.
- [ ] Django backend ingests and stores SSL metadata linked to the server.
- [ ] Main dashboard cards display an SSL badge with appropriate color-coding.
- [ ] Server side panel correctly lists all certificates discovered on the server.

## Out of Scope
- Support for non-standard certificate storage formats (e.g., Java KeyStores, Windows Cert Store).
- Proactive alerting via Email/SMS (this will be handled by the existing alerting framework in a separate or follow-up track).
- Automatic certificate renewal (the system only monitors, it does not renew).
