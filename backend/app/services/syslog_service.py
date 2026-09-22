import asyncio
from datetime import datetime
from app.services.log_service import save_log
from app.schemas.log import LogCreate

SYSLOG_HOST = "127.0.0.1"
SYSLOG_PORT = 5140  # Standard 514 requires admin rights; 5140 for dev/testing


class SyslogUDPProtocol(asyncio.DatagramProtocol):
    def datagram_received(self, data: bytes, addr: tuple):
        try:
            message = data.decode("utf-8", errors="ignore").strip()
            client_ip = addr[0]

            # Determine level based on syslog message content
            level = "Information"
            if "error" in message.lower() or "failed" in message.lower() or "critical" in message.lower():
                level = "Error"
            elif "warning" in message.lower() or "warn" in message.lower():
                level = "Warning"

            standard_log = LogCreate(
                agent_id=f"Network-{client_ip}",
                event_id=514,
                source="Network Device",
                level=level,
                log_name="Syslog",
                message=f"[{client_ip}] {message}",
                timestamp=datetime.now()
            )

            # Save to MongoDB via existing log service
            asyncio.create_task(save_log(standard_log))
            print(f"[Syslog Received] From {client_ip}: {message[:60]}...")

        except Exception as e:
            print(f"[Syslog Error] Failed to process incoming syslog packet: {e}")


async def start_syslog_server():
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: SyslogUDPProtocol(),
        local_addr=(SYSLOG_HOST, SYSLOG_PORT)
    )
    print(f"INFO:     Syslog UDP Server running on {SYSLOG_HOST}:{SYSLOG_PORT}")
    return transport