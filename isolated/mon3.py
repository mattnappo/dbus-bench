#!/usr/bin/env python3
"""
D-Bus latency monitoring script with asyncio.
Measures busctl command execution time.
"""

import asyncio
import time
import random
import signal
import json
import sys

# Generate timestamped output filename
# d = "{:%Y%m%d_%H%M%S}".format(datetime.now())
OUTPUT_FILE = sys.argv[1]


class DBusMonitor:
    """Monitor D-Bus operations and measure latency."""
    
    def __init__(self):
        self.latencies = dict()
        self.running_tasks = set()
        
    async def _run_measurement(self, task_id):
        """Wrapper to run a measurement and handle task cleanup."""
        current_task = asyncio.current_task()
        try:
            return await self.measure_busctl_latency(task_id)
        finally:
            # Remove this task from the running tasks set when it completes
            self.running_tasks.discard(current_task)

    async def measure_busctl_latency(self, task_id):
        """Measure latency of a single busctl command."""
        cmd = [
            "busctl", "get-property", 
            "org.freedesktop.systemd1", "/org/freedesktop/systemd1",
            "org.freedesktop.systemd1.Manager", "Version"
        ]
        start_time = time.time()
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await process.wait()
        end_time = time.time()
        latency = end_time - start_time
        
        # Store result and print when this specific task completes
        self.latencies[start_time] = latency
        print(f"[{start_time}] {latency:.6f} (task {task_id})")
        
        return latency
    
    async def run_monitoring_loop(self, shutdown_event):
        """Main monitoring loop that starts a new measurement every second."""
        task_id = 0
        
        try:
            while not shutdown_event.is_set():
                # Start a new measurement task without waiting for it to complete
                task_id += 1
                task = asyncio.create_task(self._run_measurement(task_id))
                self.running_tasks.add(task)
                
                # Sleep for exactly 1 second before starting the next measurement
                await asyncio.sleep(1)
                
        finally:
            await self.shutdown_gracefully()
    
    async def shutdown_gracefully(self):
        """Wait for all running tasks to complete naturally."""
        print(f"\n>>> Shutting down gracefully. Waiting for {len(self.running_tasks)} running tasks to complete...")
        
        # Wait for all running tasks to complete naturally (no cancellation)
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks, return_exceptions=True)
            
        print(">>> All tasks completed. Cleanup finished.")


async def main():
    """Main entry point."""
    monitor = DBusMonitor()
    shutdown_event = asyncio.Event()

    def signal_handler():
        print("\n>>> Ctrl+C received. Shutting down gracefully...")
        shutdown_event.set()

    # Set up signal handler for graceful shutdown
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)
    loop.add_signal_handler(signal.SIGTERM, signal_handler)

    try:
        # Create the monitoring task
        monitor_task = asyncio.create_task(monitor.run_monitoring_loop(shutdown_event))

        # Wait for either the task to complete or shutdown signal
        _done, pending = await asyncio.wait(
            [monitor_task, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if shutdown_event.is_set():
            # Shutdown was requested, wait for the monitor task to complete naturally
            try:
                await monitor_task
            except asyncio.CancelledError:
                # This shouldn't happen since we don't cancel the task
                pass
        else:
            # Normal completion (this shouldn't happen in an infinite loop)
            monitor_task.result()

        # Cancel any remaining pending tasks
        for task in pending:
            task.cancel()

    except Exception as e:
        print(f">>> Unexpected error: {e}")
    finally:
        print(f">>> Final results: {len(monitor.latencies)} measurements collected")
        
        # Convert latencies dict to a list of objects for JSON serialization
        data = []
        for timestamp, latency in monitor.latencies.items():
            data.append({
                "timestamp": timestamp,
                "latency": latency
            })
        
        # Sort by timestamp
        data.sort(key=lambda x: x["timestamp"])
        
        # Write results to timestamped JSON file
        print(f">>> Saving {len(data)} records to {OUTPUT_FILE}")
        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(">>> Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This should not happen now since we handle SIGINT in the event loop
        print("\n>>> Fallback Ctrl+C handler. Graceful shutdown may not have completed.")