"""
window.py

Copyright 2023 Cleo Menezes Jr.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

SPDX-License-Identifier: GPL-3.0-or-later
"""

from typing import Any

from escambo.collections.list_view import Collections
from escambo.define import APP_PATH, PROFILE
from gi.repository import Adw, GLib, Gtk


@Gtk.Template(resource_path=f"{APP_PATH}/ui/window.ui")
class EscamboWindow(Adw.ApplicationWindow):
    """
    A custom Adw.ApplicationWindow class for the Escambo application.
    """

    __gtype_name__ = "EscamboWindow"

    # Template objects
    stack: Gtk.Stack = Gtk.Template.Child()
    menu_add_new: Gtk.MenuButton = Gtk.Template.Child()
    sidebar_dropdown_selector: Gtk.DropDown = Gtk.Template.Child()
    status_page: Adw.StatusPage = Gtk.Template.Child()

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        self.sidebar_dropdown_selector.connect(
            "notify::selected-item", self._set_sidebar_content
        )
        self.collections = Collections()

        if PROFILE == "development":
            self.add_css_class("devel")

        self.menu_add_new.connect("activate", print, "eita")
        # Workaround to get flat design on Gtk.DropDown
        self.sidebar_dropdown_selector.get_first_child().add_css_class("flat")

    def _sidebar_has_content(self, page_title: str):
        match page_title:
            case "Collections":
                return self.collections.stored_data["collections_filenames"]

    def _set_sidebar_content(self, widget: Gtk.DropDown, _):
        page_title: str = widget.get_selected_item().get_string()

        if bool(self._sidebar_has_content(page_title)):
            self.stack.props.visible_child_name = page_title.lower()
            return None

        _title = f"No {page_title} Added"
        _description = "Click + to create."
        match page_title:
            case "Collections":
                _icon_name = "shapes-large-symbolic"
            case "Environments":
                _icon_name = "tabs-stack-symbolic"
            case "History":
                _title = f"No {page_title}"
                _description = "Any request you send will appear here."
                _icon_name = "history-undo-symbolic"

        self.stack.props.visible_child_name = "no-content"
        self.status_page.set_title(_title)
        self.status_page.set_description(_description)
        self.status_page.set_icon_name(_icon_name)
