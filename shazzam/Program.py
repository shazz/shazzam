from shazzam.Address import Address

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

    def add_label(self, label: Address):
        """add_label

        Args:
            label (Address): [description]

        Raises:
            ValueError: [description]
        """
        for existing_label_name, existing_label in self.global_labels.items():
            if existing_label_name == label.name and existing_label.value != label.value:
                raise ValueError(f"The global label {label.name} already defined at address {existing_label.value:04X}, requested: {label.address:04X}")

        self.global_labels[label.name] = label

    def get_label(self, name: str) -> Address:

        if name not in self.global_labels:
            raise ValueError(f"Cannot find the label '{name}' globally")

        return self.global_labels[name]
