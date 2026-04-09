import asyncio

from researchlens_worker.create_worker import create_worker


def main() -> None:
    worker = create_worker()
    print(worker.describe())
    asyncio.run(worker.shutdown())


if __name__ == "__main__":
    main()
