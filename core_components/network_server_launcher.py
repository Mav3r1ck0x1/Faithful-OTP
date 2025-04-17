from core_components.network_server_async import AsyncServer
from core_components.faithful_logger import notify
from core_components.message_director import MessageDirector
from core_components.client_agent import ClientAgent
'''
def main():
    logger.info("[LAUNCHER] Starting AsyncServer")
    server = AsyncServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.warning("[LAUNCHER] Server shutdown requested by user")
    except Exception as e:
        logger.exception(f"[LAUNCHER] Unhandled exception: {e}")
    finally:
        logger.info("[LAUNCHER] AsyncServer shut down")


if __name__ == "__main__":
    main()
'''

def main():
    md = MessageDirector()
    ca = ClientAgent()
    server = AsyncServer(message_director=md, client_agent=ca)
    logger.info("Starting AsyncServer...")
    asyncio.run(server.start())