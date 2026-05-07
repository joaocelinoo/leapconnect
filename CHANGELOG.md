# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.1] - 2026-05-07

### Changed

- **Updated leapmotor-api to v0.1.7**: adds support for retrieving vehicle status on the B10 model using the same method as the C10

## [0.6.0] - 2026-05-06

### Added

- **Log level control**: you can now change the logging verbosity for the app and the leapmotor-api library separately from Settings → Advanced, without restarting the application
- **Live log viewer**: a new real-time console output panel in Settings → Advanced lets you see application logs directly in the browser for easier troubleshooting. Disabled by default — enable it with a toggle when needed. Includes level filtering, text search, auto-scroll, and a live connection indicator

### Changed

- **Updated leapmotor-api to v0.1.6**

## [0.5.2] - 2026-05-05

### Added

- **Live Refresh**: new background task that automatically refreshes vehicle data at a configurable interval and pushes updates to all connected WebSocket clients — no manual refresh needed. Configurable in Settings → Services with start/stop toggle and interval selector (10–3600 seconds)
- Live Refresh is **active by default** at 30-second intervals for new installations
- Live Refresh status shown in the user menu dropdown (green dot + interval when running, grey dot + "Disabled" when off)
- `GET /api/live-refresh` and `PUT /api/live-refresh` endpoints to query and configure live refresh
- Live Refresh respects the API rate limit — uses the shared vehicle cache to avoid redundant requests

### Fixed

- **Docker build failure**: replaced `COPY --from=ghcr.io/astral-sh/uv:latest` (which required authentication) with a curl-based uv installation that works without registry access

## [0.5.1] - 2026-05-04

### Fixed

- **Messages and car image no longer crash the app**: previously, if your Leapmotor session expired or you skipped the certificate setup, opening the app would show repeated server errors (500). Now the app handles these situations gracefully and shows a clear error instead of breaking

## [0.5.0] - 2026-05-04

### Changed

- **History time filter redesigned**: replaced the period buttons (Today/7d/30d/90d) with a compact toolbar inspired by calendar apps — includes a calendar icon to open a date range picker, a label showing the selected date(s), a "Today" quick-jump pill, left/right arrows to navigate day-by-day, and a three-dot menu with CSV export
- **Date range picker**: the calendar popup now includes a "Last 12 months" preset alongside the existing quick filters (Today, Yesterday, This week/month/quarter/year, Last 7/30/90 days)
- **Removed table view toggle**: the History page now always shows charts (the chart/table switch has been removed)
- **Mobile layout**: title and description are left-aligned on mobile while the date toolbar stays centered
- **Navbar refactored**: the connection badge now shows a cloud icon with "CLOUD" / "OFFLINE" label always visible (including mobile). The refresh button and data freshness indicator are merged into a single color-coded pill. Notifications bell icon is standalone in the navbar. User avatar menu contains cloud disconnect/reconnect, Home Assistant status, and logout
- **User menu redesigned**: cleaner dropdown with improved spacing, backdrop blur, and visual hierarchy. Shows Home Assistant connection status (dot + Online/Offline/Disabled). Cloud disconnect/reconnect button explicitly labeled "Leapmotor Cloud" with confirmation dialog. Removed redundant cloud status (already in topbar badge)

### Added

- **Alembic database migrations**: added a proper migration system using Alembic. Migrations run automatically at startup (async-safe) and can also be managed via CLI (`alembic upgrade head`, `alembic history`). Existing databases are stamped at baseline and upgraded seamlessly
- **Faster History page**: the History tab now shows placeholder shapes while loading, displays summary cards first, and remembers previous data so revisiting the page feels instant
- **Smart API rate limiting**: all data requests to Leapmotor servers now go through a shared cache — no matter how many features need vehicle data (Home Assistant, history recording, dashboard), only one request is made within the configured time window. Configurable in Settings → Account with a dedicated "API Rate Limit" card (default: 10 seconds)
- **Data freshness indicator**: the top navigation bar now shows how old the displayed data is (e.g. "32s ago", "5m ago"), with color coding — green for fresh (< 2 min), yellow for stale (< 10 min), red for old data. Updates every 10 seconds
- **Real-time updates via WebSocket**: when the backend fetches fresh data from Leapmotor (via scheduler, MQTT polling, or any API call), it pushes the new vehicle status to the frontend instantly over a WebSocket connection — no manual refresh needed. The data age badge resets automatically on each push. Auto-reconnects if the connection drops
- **Cloud disconnect/reconnect**: new `POST /api/disconnect` endpoint allows disconnecting from Leapmotor Cloud without logging out — accessible from the user avatar menu with a confirmation prompt
- **Light theme**: full light mode with mint-green tinted palette inspired by the official Leapmotor app. Toggle in user menu and Settings → Preferences. Preference saved to database (default: dark)

### Fixed

- **Dynamic car image broken under HA Ingress**: the static image URL in `DynamicCarImage.vue` used an absolute path (`/api/vehicles/...`) which resolved against the Home Assistant host instead of going through the ingress proxy. Changed to a relative path (`./api/vehicles/...`) consistent with the charge frame fetch URLs
- **Power chart not displaying**: the Charging/Discharging power chart on the History page was always empty because power values were never persisted to the database. Added `charging_power_kw` and `discharge_power_kw` columns (via Alembic migration) so power data from the Leapmotor API is now saved. For historical data collected before this fix, power is derived from stored current × voltage values
- **Vampire drain chart**: added an explanatory message when no drain events are detected, instead of showing an empty chart. Explains that the battery SOC remained stable during parked sessions and describes the conditions needed to trigger the chart
- **Trip map replaced with Leaflet**: the lat/lon scatter chart is now a real interactive map (OpenStreetMap via Leaflet). Shows the route as a polyline color-coded by speed (green ≤40, orange 40–80, red >80 km/h), with Start/End markers and speed tooltips on each point. Supports dark/light tile layers based on theme, and a maximize button to expand the map to full width at 70vh height

## [0.4.1] - 2026-05-04

### Fixed

- **Reverse proxy / subpath support**: the app now works correctly behind Home Assistant Ingress or any reverse proxy that adds a path prefix — all asset and API paths are relative instead of absolute
- History page: period selector and chart/table toggle are now centered on mobile screens

## [0.4.0] - 2026-05-03

### Added

- **HTTPS support**: Docker Compose now serves the app over HTTPS (port 443) with automatic HTTP→HTTPS redirect
- Auto-generated self-signed TLS certificates: a one-shot init container creates certificates on first startup with all local IPs in the SAN, so the app is accessible via `https://<server-ip>` from any device on the network
- `generate-traefik-certs.sh` standalone script for manual certificate regeneration with support for extra IPs/hostnames as arguments
- Traefik dynamic TLS configuration (`traefik/dynamic.yml`)
- **Services setup wizard step**: after entering Leapmotor credentials, the initial setup now offers an optional step to configure Home Assistant (MQTT) and local data recording (history) before entering the app
- Users can enable/disable data recording and set the collection interval directly during first-time setup
- Users can enable Home Assistant, configure MQTT broker settings, and test the connection during first-time setup
- Both services can be skipped and configured later from Settings → Services
- **Home Assistant integration**: your vehicle data (battery, doors, climate, tires, location, and more) is now automatically shared with Home Assistant via MQTT, so you can see everything in your smart home dashboard
- In Settings → Services, you can enable Home Assistant, enter your MQTT broker details, and test the connection before saving
- All vehicle sensors appear in Home Assistant as ready-to-use entities: battery level, mileage, temperatures, tire pressures, door/window status, GPS position, live car image, and remote control buttons
- Vehicle data is sent to Home Assistant automatically every time the app collects new data
- **Separate polling timers**: history collection and Home Assistant updates now run on independent schedules — you can collect history every 15 minutes while pushing updates to HA every 30 seconds, for example
- The Home Assistant polling interval supports sub-minute values (10 sec, 30 sec, etc.) for near-real-time updates in your smart home dashboard
- **HA polling interval exposed as a Home Assistant entity**: you can adjust the polling interval directly from your HA dashboard using a slider (10 s – 3600 s), without opening the webapp
- **Charge limit controllable from Home Assistant**: a new slider entity (50%–100%) lets you set the charge limit directly from HA — the command is sent to the vehicle via the Leapmotor API
- Both ignition states are now exposed in Home Assistant: "Ignition" (key on) and "Ignition Ready" (vehicle ready to drive)
- **About page**: new dedicated "About" section in Settings with app version, GitHub links (source code, star, report issue), and a disclaimer clarifying this is an unofficial project with no affiliation to Leapmotor

### Changed

- **Settings page redesigned**: instead of a long list of cards, settings are now organized in four tabs — Account, General, Services, and Advanced — making it much easier to find what you need
- Credentials, Certificates, MQTT configuration, and Debug data now open in clean popup dialogs instead of expanding inline
- On wider screens, the Credentials and Certificates cards sit side by side in a compact grid
- Settings now use the full available width instead of being limited to a narrow column
- The app version shown in Settings is now read automatically from the project configuration, so it always stays up to date
- The Home Assistant section in Services now includes a polling interval control with +/− stepper (10 sec steps below 1 min, 1 min steps above)

### Fixed

- "Battery Charging" entity in Home Assistant no longer shows true when the car is idle — the check now uses actual charging power instead of a flag that was incorrectly set by the API library

## [0.3.0] - 2026-05-03

### Added

- User preferences system with dedicated `UserPreferences` model and `PreferencesResponse` Pydantic schema
- `GET /api/preferences` and `PUT /api/preferences` endpoints for reading/updating user preferences
- Configurable electricity price (€/kWh) in Settings → Preferences section, stored in DB (default: 0.25)
- History tab "Cost (€)" KPI now uses the user-configured electricity price instead of a hardcoded value
- The app now shows whether the vehicle is plugged in for charging, visible on the dashboard, details page, and vehicle selector
- The battery card on the dashboard now indicates the charging type: "Slow charging (AC)" or "Fast charging (DC)" based on the connection type, with a matching icon
- During setup, if certificate files are already present on the server (e.g. from a previous installation), the app detects them and offers a one-click option to reuse them instead of uploading again
- History tab: new "Today" filter shows individual snapshots (per-collection) instead of daily aggregates
- History tab: "All" filter to display the entire available history
- History tab: table view alongside charts, with toggle
- History tab: hover tooltip on charts now snaps to the nearest point with a visible indicator
- History tab: period buttons (7/30/90 days) are disabled when fewer than 2 days of data are available
- VehicleSnapshot model expanded with full telemetry: battery current/voltage, tire pressures, ignition state, locked/parked status

### Changed

- The data collection scheduler in Settings now has explicit Start/Stop buttons instead of a toggle switch
- Changing the collection interval no longer applies immediately; you pick the desired time first, then confirm with a "Set" button
- The scheduler status now shows the current interval alongside the running state (e.g. "Running · every 15 min")
- `/api/login` endpoint now reads certificate paths from the database instead of environment variables, consistent with the setup flow and auto-connect logic
- History tab defaults to "Today" period on load
- History tab labels translated to English
- SnapshotSchema API response now uses namespaced field names (e.g. `battery_expected_mileage`, `climate_outdoor_temp`) matching the internal model

### Removed

- Removed `.env` / `.env.example` and all `python-dotenv` usage; certificates are now managed entirely via the web UI (`/api/setup/certificates`); `DATA_DIR` and `HISTORY_DB_PATH` can still be set as standard environment variables (e.g. in `docker-compose.yml`)

## [0.2.0] - 2026-05-02

### Added

- **Session-based authentication**: the app now requires login with the LeapConnect password before accessing any data; other devices can no longer auto-enter without authenticating
- `POST /api/auth/login` endpoint: authenticates with LeapConnect user password and sets an HttpOnly session cookie (7-day expiry)
- `POST /api/auth/logout` endpoint: invalidates the session and clears the cookie
- HTTP middleware that blocks all `/api/` routes (except `/api/setup/status`, `/api/setup/user`, `/api/auth/login`) without a valid session cookie
- `LoginView.vue`: password-only login screen shown to returning users who don't have a valid session
- `authenticated` field in `SetupStatusResponse` schema
- `AuthLoginResponse` schema for the login endpoint
- Auto-login on first-time user creation (session cookie set by `POST /api/setup/user`)
- 401 response handler in the frontend API composable — expired sessions redirect to login automatically
- `auth_client` test fixture and session-aware tests (`test_status_requires_session`, `test_vehicles_requires_session`, `test_auth_login_wrong_password`)
- Tests now use a temporary DB (`tmp_path`) to avoid stale state between runs
- Separate LeapConnect user account from Leapmotor API credentials: first-time setup flow is now User → Certificates → Leapmotor credentials
- `UserSetupView.vue`: new first-time setup screen to create a LeapConnect account (display name + password)
- `leapconnect_users` DB table with hashed passwords (PBKDF2-SHA256 + salt) for local account management
- Backend endpoints: `POST /api/setup/user` (create), `GET /api/setup/user` (info), `PUT /api/setup/user` (update with password verification)
- Settings now has 3 separate editable sections: LeapConnect Account, Leapmotor Credentials, Certificates
- Certificate status indicators (installed/missing) in Settings
- `ClimateControlModal` component: consolidated A/C Toggle, Quick Cool, Quick Heat, and Defrost into a single "Climate" modal with quick-action buttons and full parameter controls (temperature 16–32°C, fan level 1–7, mode cool/heat/fan, operate auto/manual, air circulation recirculate/fresh, windshield normal/defrost)
- Backend `ClimateRequest` model with optional climate parameters (`circle`, `mode`, `operate`, `position`, `temperature`, `windlevel`, `wshld`)
- Message notification dropdown in the top navbar with unread badge, inline message preview, infinite scroll, and periodic polling (60s)
- Unread indicator dot on the Messages tab icon in both the sidebar and bottom tab bar
- `unreadMessages` reactive state and `loadUnreadCount()` action in the app store
- `WindowControlModal` component: merged open/close windows into a single control with quick-action buttons and a horizontal slider (0–100%) for precise window positioning; displays per-window state indicators (4 colored dots) with legend
- `SunshadeControlModal` component: merged open/close sunshade into a single control with quick-action buttons and a horizontal slider (0–10) for precise sunshade positioning; shows current sunshade state indicator on the track
- Backend `POST /api/vehicles/{vin}/windows` endpoint accepting a `value` parameter (0–100) for arbitrary window position
- Backend `POST /api/vehicles/{vin}/sunshade` endpoint accepting a `value` parameter (0–10) for arbitrary sunshade position
- `execControl()` in the store now supports an optional request body for parameterized commands
- Active state dot indicator on remote control buttons (pulsing colored dot) for trunk open, lock/unlock, and A/C status
- Raw data viewer in Settings tab with tabbed UI (Vehicle / Status) showing the unprocessed API responses for both `Vehicle.raw` and `VehicleStatus.raw`
- `vehicle_raw` and `status_raw` fields in `FullVehicleDataResponse` API schema
- `raw` field in `VehicleSchema` and `VehicleStatusSchema`

### Changed

- Logout now clears the LeapConnect session only, without disconnecting the Leapmotor API (the background scheduler continues collecting data); user is redirected to the login screen
- All frontend API requests now include `credentials: 'include'` for cookie-based session handling
- Setup flow now requires creating a LeapConnect user first, then uploading certificates, then adding Leapmotor credentials (previously certificates → credentials only)
- Settings "Account" section split into three: LeapConnect Account (display name, password), Leapmotor Credentials (email, password), Certificates (cert/key upload)
- `SetupStatusResponse` and `ConnectionStatusResponse` now include `has_user` and `display_name` fields
- Climate remote controls consolidated from four separate buttons (A/C Toggle, Quick Cool, Quick Heat, Defrost) into a single "Climate" button that opens a dedicated modal; quick actions remain available inside the modal
- Backend climate endpoints (`ac`, `quick-cool`, `quick-heat`, `defrost`) now accept an optional `ClimateRequest` body to forward parameters to the leapmotor-api client
- Window and sunshade remote controls consolidated from two separate buttons each into a single button that opens a dedicated modal
- Removed "Close Trunk" button (not supported); trunk control is now a single "Open Trunk" button with `PackageOpen` icon
- Existing `windows/open`, `windows/close`, `sunshade/open`, `sunshade/close` endpoints now accept an optional `value` body parameter to override defaults
- All FastAPI endpoints now declare `response_model` with typed Pydantic schemas where applicable, enabling automatic validation and OpenAPI documentation
- Added concise docstrings to every API endpoint
- Added return type annotations to all endpoint functions
- New response wrapper schemas: `FullVehicleDataResponse`, `VehicleHistoryResponse`, `DailySummaryResponse`, `SchedulerStatusResponse`, `MessageListResponse`, `UnreadCountResponse`, and others
- Certificate setup page now supports drag & drop for certificate and key file uploads
- New `schemas.py` file with Pydantic models for all API responses (vehicle, status, messages), each with a `from_model` method for easy conversion
- Migrated from pip/venv to uv (Astral) for dependency and environment management
- Replaced `requirements.txt` with `uv.lock` for deterministic builds
- Updated Dockerfile to use uv for dependency installation
- Updated `requires-python` from `>=3.11` to `>=3.12` (required by leapmotor-api)
- Updated leapmotor-api dependency to v0.1.2
- `bump-my-version` for automated versioning across `pyproject.toml` and `frontend/package.json`
- Pre-commit hooks: trailing whitespace, end-of-file fixer, YAML/TOML/JSON validation, ruff lint + format
- Pre-push hook: pytest suite must pass before pushing
- Test suite with pytest + pytest-asyncio
- `.python-version` file (3.13)
- Added menu to read messages from leapmotor account

### Fixed

- Charging status in the frontend now uses the vehicle-level `is_charging` property instead of the battery-level one, which was incorrectly showing charging during regenerative braking
- Swap icons for window controls to match action labels

### Changed

- Endpoints now return Pydantic model instances directly instead of manually calling `.model_dump()`; FastAPI handles serialization via `response_model`
- Vehicle data now uses structured response schemas, making the API output consistent and complete with the underlying vehicle model
- All vehicle properties (doors, windows, tires, connectivity, ignition, etc.) now use their original field names instead of shortened aliases
- The vehicle nickname field is now returned as `vehicle_nickname` to match the data source
- Tire pressure data now includes both raw kPa values and converted bar values, plus a status indicator for each wheel
- Battery information now exposes all available fields, including raw energy in Wh and converted kWh
- Climate, door, window, and connectivity sections now include all available data points instead of a subset
- Updated the entire frontend to work with the new field names
- Moved data models (snapshot, scheduler settings) to a dedicated file for better organization
- Moved the background data collection scheduler to a separate `services` folder, keeping storage-related code separate from application logic

### Removed

- Removed manual data conversion helpers in favor of Pydantic response schemas

## [0.1.0] - 2026-05-01

### Added

- Live vehicle status: battery, range, speed, odometer, temperature, lock status
- Remote controls: lock/unlock, trunk, windows, sunshade, climate (A/C, quick cool/heat, defrost), battery preheat, find car
- Adjustable charge limit slider
- Vehicle details: doors, windows, tire pressure, climate, connectivity, ignition
- Location: OpenStreetMap embedded view with coordinates
- Mileage & energy delivery history
- Car picture view link
- Raw data viewer for debugging
- Multi-vehicle tab switching
- Docker Compose deployment with Traefik reverse proxy
- SQLite-based vehicle history persistence
- Certificate-based authentication setup flow
