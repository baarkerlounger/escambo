from escambo.define import APP_ID, APP_PATH
from gi.repository import Gio, Gtk

from .create_data import create_and_store_data
from .model import DataObject


@Gtk.Template(resource_path=f"{APP_PATH}/ui/collections.ui")
class Collections(Gtk.ScrolledWindow):
    __gtype_name__ = "Collections"

    # Template objects
    list_view: Gtk.ListView = Gtk.Template.Child()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.settings = Gio.Settings.new(APP_ID)
        # print(self.settings.get_strv("collections-list"))

        _factory = Gtk.SignalListItemFactory()
        _factory.connect("setup", self.setup)
        _factory.connect("bind", self.bind)
        self.list_view.set_factory(_factory)

        store = Gio.ListStore.new(DataObject)
        self.model = Gtk.TreeListModel.new(
            store, False, False, self.add_tree_node
        )
        _selection = Gtk.SingleSelection.new(self.model)
        _selection.connect("selection-changed", self.eita)
        self.list_view.set_model(_selection)

        self.stored_data = create_and_store_data(store)

    def add_tree_node(
        self, item: "DataObject"
    ) -> Gtk.TreeListModel | Gio.ListStore:
        if not (item):
            return self.model
        else:
            if type(item) == Gtk.TreeListRow:
                item = item.get_item()

            if not item.children:
                return None
            _store = Gio.ListStore.new(DataObject)
            for child in item.children:
                _store.append(child)
            return _store

    def eita(self, widget, item, n):
        ...
        print(widget.props.selected_item.get_item().path)
        # print(item)
        # print(widget.get_model())
        # print(item)
        # print(n)

    def setup(
        self, widget: Gtk.SignalListItemFactory, item: Gtk.ListItem
    ) -> None:
        """Setup the widget to show in the Gtk.Listview"""

        main_container = Gtk.Box(spacing=6)
        icon_badge_container = Gtk.Box()

        icon_badge_container.append(
            Gtk.Image(icon_size="normal", icon_name="folder-symbolic")
        )
        icon_badge_container.append(
            Gtk.Label(css_classes=["badge-listview-method"], valign="center")
        )
        main_container.append(icon_badge_container)
        main_container.append(Gtk.Label(ellipsize="PANGO_ELLIPSIZE_END"))
        expander = Gtk.TreeExpander(child=main_container)
        item.set_child(expander)
        
    def bind(
        self, widget: Gtk.SignalListItemFactory, item: Gtk.ListItem
    ) -> None:
        """bind data from the store object to the widget"""
        expander: Gtk.TreeExpander = item.get_child()
        main_box = expander.get_child()
        icon_badge_box = main_box.get_first_child()

        icon: Gtk.Image = icon_badge_box.get_first_child()
        badge: Gtk.Label = icon_badge_box.get_last_child()
        label: Gtk.Label = main_box.get_last_child()
        row: Gtk.TreeListRow = item.get_item()

        expander.set_list_row(row)
        obj: DataObject = row.get_item()

        not obj.icon_or_badge and icon.hide()
        if not obj.icon_or_badge and not obj.method:
            label.add_css_class("heading")
        if not obj.method:
            badge.hide()
        else:
            badge.set_label(obj.method)
            badge.add_css_class(f"{obj.method.lower()}-badge")

        label.set_label(obj.data)
        label.set_tooltip_text(obj.data)
