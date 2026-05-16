"""Persistence layer data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

DEFAULT_INTERVAL_MINUTES = 15


@dataclass(frozen=True, slots=True)
class VehicleSnapshot:
    """A single point-in-time snapshot of vehicle telemetry."""

    vin: str
    timestamp: datetime

    # Battery
    battery_soc: int | None = None
    battery_current: float | None = None
    battery_voltage: float | None = None
    battery_charging_power_kw: float | None = None
    battery_discharge_power_kw: float | None = None
    battery_is_charging: bool | None = None
    battery_is_discharging: bool | None = None
    battery_dump_energy: float | None = None
    battery_expected_mileage: int | None = None
    battery_charge_state: int | None = None

    # Drive
    drive_is_parked: bool | None = None
    drive_speed: int | None = None
    drive_total_mileage: int | None = None

    # Ignition
    ignition_is_on1: bool | None = None
    ignition_is_on2: bool | None = None

    # Vehicle
    vehicle_is_charging: bool | None = None
    vehicle_is_plugged: bool | None = None
    vehicle_is_regening: bool | None = None
    vehicle_is_parked: bool | None = None
    vehicle_is_locked: bool | None = None
    vehicle_latitude: float | None = None
    vehicle_longitude: float | None = None

    # Climate
    climate_outdoor_temp: int | None = None

    # Tire
    tire_front_left_pressure: float | None = None
    tire_front_right_pressure: float | None = None
    tire_rear_left_pressure: float | None = None
    tire_rear_right_pressure: float | None = None


@dataclass
class UserPreferences:
    """User-configurable preferences."""

    electricity_price_kwh: float = 0.25
    theme: str = "dark"


@dataclass
class SchedulerSettings:
    """User-facing scheduler configuration."""

    enabled: bool = False
    interval_minutes: int = DEFAULT_INTERVAL_MINUTES
    mqtt_interval_seconds: int = 60
    rate_limit_seconds: int = 10


@dataclass
class LiveRefreshSettings:
    """Live refresh configuration for WebSocket-connected clients."""

    interval_seconds: int = 30  # 0 = disabled, default 30s


@dataclass
class MqttSettings:
    """MQTT connection settings for Home Assistant integration."""

    enabled: bool = False
    broker: str = ""
    port: int = 1883
    username: str = ""
    password: str = ""
    use_tls: bool = False
    discovery_prefix: str = "homeassistant"
    topic_prefix: str = "leapconnect"


@dataclass
class AbrpSettings:
    """ABRP (A Better Route Planner) telemetry settings."""

    enabled: bool = False
    user_token: str = ""
