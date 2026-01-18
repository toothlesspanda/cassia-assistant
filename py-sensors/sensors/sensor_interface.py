import abc


class SensorInterface:
    @abc.abstractmethod
    def run(self):
        pass

    def build_json_payload(self):
        pass
