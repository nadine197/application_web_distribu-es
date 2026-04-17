"""
Minimal Eureka client — registers/deregisters the service on Netflix Eureka.
Uses the REST API directly (no Java SDK needed).
"""

import asyncio
import logging
import socket
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class EurekaClient:

    def __init__(
        self,
        app_name: str,
        instance_host: str,
        instance_port: int,
        eureka_url: str,
        heartbeat_interval: int = 30,
    ):
        self.app_name           = app_name.upper()
        self.instance_host      = instance_host
        self.instance_port      = instance_port
        self.eureka_url         = eureka_url.rstrip("/")
        self.heartbeat_interval = heartbeat_interval
        self.instance_id        = f"{instance_host}:{app_name}:{instance_port}"
        self._heartbeat_task: Optional[asyncio.Task] = None

    # ── Public API ────────────────────────────────────────────────────────────

    async def register(self) -> None:
        payload = self._build_registration_payload()
        url = f"{self.eureka_url}/apps/{self.app_name}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code in (200, 204):
                    logger.info(f"Registered '{self.app_name}' on Eureka ({self.eureka_url})")
                else:
                    logger.warning(f"Eureka registration returned {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.warning(f"Could not register on Eureka: {e}")

        # Start heartbeat loop
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def deregister(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        url = f"{self.eureka_url}/apps/{self.app_name}/{self.instance_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                await client.delete(url)
                logger.info(f"Deregistered '{self.app_name}' from Eureka")
            except Exception as e:
                logger.warning(f"Could not deregister from Eureka: {e}")

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        """Send heartbeat every N seconds to keep the registration alive."""
        url = f"{self.eureka_url}/apps/{self.app_name}/{self.instance_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                try:
                    resp = await client.put(url)
                    if resp.status_code not in (200, 404):
                        logger.warning(f"Eureka heartbeat: {resp.status_code}")
                    # If 404, re-register
                    if resp.status_code == 404:
                        await self.register()
                except Exception as e:
                    logger.warning(f"Eureka heartbeat failed: {e}")

    def _build_registration_payload(self) -> dict:
        ip = self._get_local_ip()
        return {
            "instance": {
                "instanceId":  self.instance_id,
                "hostName":    self.instance_host,
                "app":         self.app_name,
                "ipAddr":      ip,
                "status":      "UP",
                "overriddenStatus": "UNKNOWN",
                "port": {
                    "$":        self.instance_port,
                    "@enabled": "true",
                },
                "securePort": {
                    "$":        443,
                    "@enabled": "false",
                },
                "countryId": 1,
                "dataCenterInfo": {
                    "@class": "com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo",
                    "name":   "MyOwn",
                },
                "leaseInfo": {
                    "renewalIntervalInSecs": self.heartbeat_interval,
                    "durationInSecs":        90,
                },
                "metadata": {"management.port": str(self.instance_port)},
                "homePageUrl":   f"http://{self.instance_host}:{self.instance_port}/",
                "statusPageUrl": f"http://{self.instance_host}:{self.instance_port}/actuator/info",
                "healthCheckUrl":f"http://{self.instance_host}:{self.instance_port}/actuator/health",
                "vipAddress":    self.app_name.lower(),
                "isCoordinatingDiscoveryServer": "false",
                "lastUpdatedTimestamp": "0",
                "lastDirtyTimestamp":   "0",
            }
        }

    @staticmethod
    def _get_local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
        finally:
            s.close()
