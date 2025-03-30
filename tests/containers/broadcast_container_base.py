from tests.containers.permitContainer import PermitContainer


class BroadcastContainerBase(PermitContainer):
    def __init__(self):
        PermitContainer.__init__(self)

    def get_url(self) -> str:
        url = ""

        match self.settings.protocol:
            case "redis":
                url = (
                    self.settings.protocol
                    + "://"
                    + self.settings.container_name
                    + ":"
                    + str(self.settings.port)
                )
                print(url)
                return url
            case "postgres":
                url = (
                    self.settings.protocol
                    + "://"
                    + self.settings.user
                    + ":"
                    + self.settings.password
                    + "@"
                    + self.settings.container_name
                    + ":"
                    + str(self.settings.port)
                )
                print(url)
                return url
            case "kafka":
                url = (
                    self.settings.protocol
                    + "://"
                    + self.settings.kafka_container_name
                    + ":"
                    + str(self.settings.kafka_port)
                )
                print(url)
                return url

            case _:
                raise ValueError(f"Unknown broadcast container type: {self.settings}")
        print(url)
        return url
