# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **History tab UX improvements**: skeleton screens, progressive loading, and stale-while-revalidate caching
  - Skeleton placeholders (shimmer animation) shown for KPI cards, charts, and table while data loads
  - Progressive loading: KPI cards appear immediately, charts render after data is ready
  - Stale-while-revalidate: cached data from sessionStorage is shown instantly on revisit while fresh data is fetched in background, with a subtle "Updating data..." indicator

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
