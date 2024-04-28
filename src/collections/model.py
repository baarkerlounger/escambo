from gi.repository import GObject


class DataObject(GObject.GObject):
    def __init__(
        self,
        txt: str,
        is_folder: bool = False,
        method: str = "",
        children=None,
        path: list = [],
    ) -> None:
        super(DataObject, self).__init__()
        self.data: str = txt
        self.children: str = children
        self.icon_or_badge: str = is_folder
        self.method = method
        self.path = path
