import asyncio
import signal

from researchlens_worker.create_worker import create_worker


async def _run_worker() -> None:
    worker = create_worker()
    print(worker.describe())
    loop = asyncio.get_running_loop()
    for signal_name in ("SIGINT", "SIGTERM"):
        signal_value = getattr(signal, signal_name, None)
        if signal_value is None:
            continue
        try:
            loop.add_signal_handler(signal_value, worker.stop)
        except NotImplementedError:
            pass
    await worker.run()


def main() -> None:
    try:
        asyncio.run(_run_worker())
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
