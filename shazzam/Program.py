class Program():

    def __init__(self):
        self.segments = []
        self.global_labels = {}
        self.name = ""

    def set_name(self, name: str) -> None:
        """set_name

        Args:
            name (str): [description]
        """
        self.name = name

    def add_label(self, label: str, address: int):
        """add_label

        Args:
            label (str): [description]
            address (int): [description]

        Raises:
            ValueError: [description]
        """
        for existing_label, adr in self.global_labels.items():
            if existing_label == label and adr != address:
                raise ValueError(f"The global label {label} already defined at address {adr:04X}, requested: {address:04X}")

        self.global_labels[label] = address