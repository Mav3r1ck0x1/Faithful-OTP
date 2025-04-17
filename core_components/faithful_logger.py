import logging
import coloredlogs

class faithfulLogger(object):
    def __init__(self, category):
        self.logger = logging.getLogger(category)
        self.logger.setLevel(logging.DEBUG)
        self.handler = logging.StreamHandler()
        self.handler.setLevel(logging.DEBUG)
        #self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s]: %(message)s')  # No hostname here
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        #coloredlogs.install(level='DEBUG', logger=self.logger)
        coloredlogs.install(level='DEBUG', logger=self.logger, fmt='%(asctime)s [%(levelname)s] [%(name)s]: %(message)s')
        self.logger.propagate = False


    def faithfulInfo(self, message):
        self.logger.info(message)

    def faithfulWarning(self, message):
        self.logger.warning(message)

    def faithfulError(self, message):
        self.logger.error(message)

    def faithfulDebug(self, message):
        self.logger.debug(message)

class LoggerNotify(object):
    def __init__(self):
        self.categories = {}

    def new_category(self, category):
        if category not in self.categories:
            notifier = faithfulLogger(category)
            self.categories[category] = notifier
        return self.categories[category]


notify = LoggerNotify()

DC_logger = notify.new_category("NetworkDCLoader")
DC_logger.faithfulInfo("This is an info message for testing.")

MDClient = notify.new_category("MDClient")



    