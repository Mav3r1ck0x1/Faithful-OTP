from core_components.faithful_logger import notify

class ClientAgent:
    logger = notify.new_category("CA")

    def __init__(self, otp):
        self.otp = otp
        self.clients = []

    def handle(self, channels, sender, code, datagram):
        print(f"[CA] Handling message from {sender} with code {code}")
        # You could parse code types here and route accordingly

    def handle_client_message(self, data, writer):
        """
        Handle a message received from a client (asynchronously handled by another component).
        """
        try:
            message = data.decode()
            addr = writer.get_extra_info('peername')

            self.logger.debug(f"Received message {message} from {addr}")

            # Process the message (e.g., forward it to other components)
            self.process_message(message, writer)

        except Exception as e:
            self.logger.error(f"Error processing client message: {e}")

    def process_message(self, message, writer):
        """
        Process the client message and prepare a response.
        """
        response = f"Server received: {message}"
        
        writer.write(response.encode())  # Send the response asynchronously
        self.logger.debug(f"Sent response: {response}")

