
from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from monitor.consumers import StatusConsumer
from asgiref.sync import async_to_sync
import asyncio

class StatusConsumerTest(TransactionTestCase):
    def test_status_consumer_metrics_update(self):
        async def run_test():
            communicator = WebsocketCommunicator(StatusConsumer.as_asgi(), "/ws/status/")
            connected, _ = await communicator.connect()
            if not connected:
                return False

            # Receive initial snapshot
            await communicator.receive_json_from()

            # Simulate a server.metrics message from channel layer
            server_data = {
                "id": 1,
                "last_cpu_percent": 75.0,
                "last_ram_percent": 80.0,
                "last_disk_percent": 45.0
            }
            
            # Use the internal handler
            await communicator.send_input({
                "type": "server.metrics",
                "server": server_data
            })

            response = await communicator.receive_json_from()
            assert response["type"] == "metrics_update"
            assert response["server"]["last_cpu_percent"] == 75.0
            
            await communicator.disconnect()
            return True

        self.assertTrue(asyncio.run(run_test()))
