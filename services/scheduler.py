"""Background scheduler for periodic vehicle data collection.

Runs as an asyncio task inside the FastAPI process. Polls all connected
vehicles at a configurable interval and persists snapshots via the
repository port.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from models import SchedulerSettings, VehicleSnapshot

if TYPE_CHECKING:
    from leapmotor_api.async_client import AsyncLeapmotorApiClient
    from leapmotor_api.models import Vehicle

    from persistence.repository import VehicleHistoryRepository

_LOGGER = logging.getLogger(__name__)

MIN_INTERVAL_MINUTES = 1
MAX_INTERVAL_MINUTES = 1440  # 24 h
MIN_MQTT_INTERVAL_SECONDS = 10
MAX_MQTT_INTERVAL_SECONDS = 86400  # 24 h


class VehicleDataScheduler:
    """Periodically polls vehicle status and saves snapshots."""

    def __init__(
        self,
        repo: VehicleHistoryRepository,
    ) -> None:
        self._repo = repo
        self._settings = SchedulerSettings()
        self._history_task: asyncio.Task | None = None
        self._mqtt_task: asyncio.Task | None = None
        self._history_stop = asyncio.Event()
        self._mqtt_stop = asyncio.Event()
        self._last_run: datetime | None = None
        self._last_error: str | None = None
        self._total_runs: int = 0
        self._total_errors: int = 0

        # Injected at runtime by main.py when the user logs in
        self._client: AsyncLeapmotorApiClient | None = None
        self._vehicles: list[Vehicle] = []

        # Optional callback for publishing status (e.g. MQTT)
        self._on_status_callback = None

    # -- public API ----------------------------------------------------------

    @property
    def settings(self) -> SchedulerSettings:
        return self._settings

    @property
    def is_running(self) -> bool:
        history_running = (
            self._history_task is not None and not self._history_task.done()
        )
        mqtt_running = self._mqtt_task is not None and not self._mqtt_task.done()
        return history_running or mqtt_running

    def status_dict(self) -> dict:
        return {
            "enabled": self._settings.enabled,
            "interval_minutes": self._settings.interval_minutes,
            "mqtt_interval_seconds": self._settings.mqtt_interval_seconds,
            "is_running": self.is_running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "last_error": self._last_error,
            "total_runs": self._total_runs,
            "total_errors": self._total_errors,
        }

    def set_client(
        self, client: AsyncLeapmotorApiClient | None, vehicles: list[Vehicle]
    ) -> None:
        self._client = client
        self._vehicles = vehicles

    def set_on_status_callback(self, callback) -> None:
        """Set a callback invoked with (vehicle, status) after each MQTT poll."""
        self._on_status_callback = callback

    def update_settings(
        self,
        *,
        enabled: bool | None = None,
        interval_minutes: int | None = None,
        mqtt_interval_seconds: int | None = None,
    ) -> SchedulerSettings:
        if interval_minutes is not None:
            interval_minutes = max(
                MIN_INTERVAL_MINUTES, min(MAX_INTERVAL_MINUTES, interval_minutes)
            )
            self._settings.interval_minutes = interval_minutes
        if mqtt_interval_seconds is not None:
            mqtt_interval_seconds = max(
                MIN_MQTT_INTERVAL_SECONDS,
                min(MAX_MQTT_INTERVAL_SECONDS, mqtt_interval_seconds),
            )
            self._settings.mqtt_interval_seconds = mqtt_interval_seconds
        if enabled is not None:
            self._settings.enabled = enabled

        # Apply change immediately
        if self._settings.enabled:
            self._ensure_running()
        else:
            self._request_stop()

        return self._settings

    def start(self) -> None:
        if self._settings.enabled:
            self._ensure_running()

    async def stop(self) -> None:
        self._request_stop()
        for task in (self._history_task, self._mqtt_task):
            if task and not task.done():
                with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                    await asyncio.wait_for(task, timeout=5)
        self._history_task = None
        self._mqtt_task = None

    # -- internals -----------------------------------------------------------

    def _ensure_running(self) -> None:
        # History loop
        if self._history_task and not self._history_task.done():
            self._history_stop.set()
        else:
            self._history_stop.clear()
            self._history_task = asyncio.create_task(
                self._history_loop(), name="scheduler-history"
            )
        # MQTT loop
        if self._mqtt_task and not self._mqtt_task.done():
            self._mqtt_stop.set()
        else:
            self._mqtt_stop.clear()
            self._mqtt_task = asyncio.create_task(
                self._mqtt_loop(), name="scheduler-mqtt"
            )

    def _request_stop(self) -> None:
        self._history_stop.set()
        self._mqtt_stop.set()

    async def _history_loop(self) -> None:
        _LOGGER.info(
            "Scheduler started (history interval=%d min)",
            self._settings.interval_minutes,
        )
        try:
            while self._settings.enabled:
                await self._poll_history()
                try:
                    await asyncio.wait_for(
                        self._history_stop.wait(),
                        timeout=self._settings.interval_minutes * 60,
                    )
                    self._history_stop.clear()
                except TimeoutError:
                    pass
        except asyncio.CancelledError:
            pass
        finally:
            _LOGGER.info("Scheduler history loop stopped")

    async def _mqtt_loop(self) -> None:
        _LOGGER.info(
            "Scheduler started (MQTT interval=%d sec)",
            self._settings.mqtt_interval_seconds,
        )
        try:
            while self._settings.enabled:
                await self._poll_mqtt()
                try:
                    await asyncio.wait_for(
                        self._mqtt_stop.wait(),
                        timeout=self._settings.mqtt_interval_seconds,
                    )
                    self._mqtt_stop.clear()
                except TimeoutError:
                    pass
        except asyncio.CancelledError:
            pass
        finally:
            _LOGGER.info("Scheduler MQTT loop stopped")

    async def _poll_history(self) -> None:
        """Poll vehicles and save snapshots to the history DB."""
        if not self._client or not self._vehicles:
            _LOGGER.debug("Scheduler: no client or vehicles, skipping history poll")
            return

        _LOGGER.info(
            "Scheduler: polling %d vehicle(s) for history", len(self._vehicles)
        )
        self._total_runs += 1
        self._last_run = datetime.utcnow()
        self._last_error = None

        for vehicle in self._vehicles:
            try:
                status = await self._client.get_vehicle_status(vehicle)
                snapshot = VehicleSnapshot(
                    vin=vehicle.vin,
                    timestamp=status.collect_time or datetime.utcnow(),
                    battery_soc=status.battery.soc,
                    battery_current=status.battery.battery_current,
                    battery_voltage=status.battery.battery_voltage,
                    battery_is_charging=status.is_charging,
                    battery_dump_energy=status.battery.dump_energy,
                    battery_expected_mileage=status.battery.expected_mileage,
                    battery_charge_state=status.battery.charge_state.value
                    if status.battery.charge_state
                    else None,
                    drive_is_parked=status.driving.is_parked,
                    drive_speed=status.driving.speed,
                    drive_total_mileage=status.driving.total_mileage,
                    vehicle_is_charging=status.is_charging,
                    vehicle_is_plugged=status.is_plugged,
                    vehicle_is_parked=status.is_parked,
                    vehicle_is_locked=status.is_locked,
                    vehicle_latitude=status.location.latitude,
                    vehicle_longitude=status.location.longitude,
                    climate_outdoor_temp=status.climate.outdoor_temp,
                    tire_front_left_pressure=status.tires.front_left_kpa
                    if status.tires
                    else None,
                    tire_front_right_pressure=status.tires.front_right_kpa
                    if status.tires
                    else None,
                    tire_rear_left_pressure=status.tires.rear_left_kpa
                    if status.tires
                    else None,
                    tire_rear_right_pressure=status.tires.rear_right_kpa
                    if status.tires
                    else None,
                )
                await self._repo.save_snapshot(snapshot)
                _LOGGER.info(
                    "Scheduler: saved snapshot for %s (SOC=%s%%)",
                    vehicle.vin,
                    status.battery.soc,
                )
            except Exception as exc:
                self._total_errors += 1
                self._last_error = f"{vehicle.vin}: {exc}"
                _LOGGER.exception("Scheduler: failed to poll %s", vehicle.vin)

    async def _poll_mqtt(self) -> None:
        """Poll vehicles and publish status to MQTT listeners."""
        if not self._client or not self._vehicles:
            _LOGGER.debug("Scheduler: no client or vehicles, skipping MQTT poll")
            return
        if not self._on_status_callback:
            return

        _LOGGER.info("Scheduler: polling %d vehicle(s) for MQTT", len(self._vehicles))

        for vehicle in self._vehicles:
            try:
                status = await self._client.get_vehicle_status(vehicle)
                await self._on_status_callback(vehicle, status)
            except Exception:
                _LOGGER.debug("Scheduler: MQTT poll failed for %s", vehicle.vin)
