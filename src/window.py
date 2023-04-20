# window.py
#
# Copyright 2022 Cleo Menezes Jr.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import html
import json
import os
import threading
from datetime import datetime as dt
from typing import Callable

from getoverhere.check_url import has_parameter, is_valid_url
from getoverhere.date_row import DateRow
from getoverhere.dialog_cookies import CookieDialog
from getoverhere.dialog_headers import HeaderDialog
from getoverhere.populator_entry import PupulatorEntry
from getoverhere.restapi import ResolveRequests
from getoverhere.sourceview import SourceView
from gi.repository import Adw, Gio, GLib, Gtk
from requests import Session, exceptions

# constants
COOKIES = os.path.join(
    GLib.get_user_config_dir(), "getoverhere", "cookies.json"
)
BODY = os.path.join(GLib.get_user_config_dir(), "getoverhere", "body.json")
PARAM = os.path.join(
    GLib.get_user_config_dir(), "getoverhere", "parameters.json"
)
HEADERS = os.path.join(
    GLib.get_user_config_dir(), "getoverhere", "headers.json"
)
AUTHS = os.path.join(GLib.get_user_config_dir(), "getoverhere", "auths.json")


@Gtk.Template(
    resource_path="/io/github/cleomenezesjr/GetOverHere/gtk/window.ui"
)
class GetoverhereWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GetoverhereWindow"

    # Template objects
    toast_overlay = Gtk.Template.Child()
    leaflet = Gtk.Template.Child()

    entry_method = Gtk.Template.Child()
    entry_url = Gtk.Template.Child()

    response_stack = Gtk.Template.Child()
    response_page = Gtk.Template.Child()
    response_page_header = Gtk.Template.Child()
    raw_page_body = Gtk.Template.Child()
    form_data_page_body = Gtk.Template.Child()

    response_source_view: SourceView = Gtk.Template.Child()
    raw_source_view_body: SourceView = Gtk.Template.Child()

    btn_response_go_back = Gtk.Template.Child()
    btn_raw_go_back_body = Gtk.Template.Child()
    btn_form_data_go_back_body = Gtk.Template.Child()

    home = Gtk.Template.Child()
    form_data_toggle_button_body = Gtk.Template.Child()
    btn_edit_body = Gtk.Template.Child()

    btn_send_request = Gtk.Template.Child()

    entry_body_key = Gtk.Template.Child()
    entry_body_value = Gtk.Template.Child()
    btn_add_body = Gtk.Template.Child()
    group_overrides_body = Gtk.Template.Child()
    counter_label_form_data_body = Gtk.Template.Child()

    entry_param_key = Gtk.Template.Child()
    entry_param_value = Gtk.Template.Child()
    btn_add_parameter = Gtk.Template.Child()
    expander_row_parameters = Gtk.Template.Child()
    btn_edit_param = Gtk.Template.Child()
    btn_edit_param_go_back = Gtk.Template.Child()
    form_data_page_parameters = Gtk.Template.Child()
    group_overrides_param = Gtk.Template.Child()

    switch_cookie = Gtk.Template.Child()
    cookies_page = Gtk.Template.Child()
    create_new_cookie = Gtk.Template.Child()
    group_overrides_cookies = Gtk.Template.Child()

    switch_headers = Gtk.Template.Child()
    headers_page = Gtk.Template.Child()
    create_new_header = Gtk.Template.Child()
    group_overrides_headers = Gtk.Template.Child()

    auths_page = Gtk.Template.Child()
    auth_type = Gtk.Template.Child()
    api_key_auth_key = Gtk.Template.Child()
    api_key_auth_value = Gtk.Template.Child()
    api_key_auth_add_to = Gtk.Template.Child()
    api_key_prefs = Gtk.Template.Child()
    bearer_token_prefs = Gtk.Template.Child()
    bearer_token = Gtk.Template.Child()

    spinner = Gtk.Template.Child()

    def __init__(self, **kwargs: dict) -> None:
        super().__init__(**kwargs)

        self.kwargs = kwargs
        # Ensure close session
        with Session() as session:
            self.session = session

        # Connect signals
        self.btn_send_request.connect("clicked", self.__on_send)
        self.btn_edit_body.connect("activated", self.__on_edit, "body")
        self.btn_edit_param.connect("activated", self.__on_edit, "param")
        # TODO call from template
        self.create_new_cookie.connect(
            "activated", self._show_cookie_dialog, "New Cookie"
        )
        self.create_new_header.connect(
            "activated", self._show_header_dialog, "New Header"
        )
        self.api_key_auth_key.connect(
            "apply", self.on_auth_entry_active, "api_key_auth_key"
        )
        self.api_key_auth_value.connect(
            "apply", self.on_auth_entry_active, "api_key_auth_value"
        )
        self.bearer_token.connect(
            "apply", self.on_auth_entry_active, "bearer_token"
        )
        self.switch_cookie.connect("state-set", self.set_needs_attention)
        self.btn_add_body.connect("clicked", self.__save_override, "body")
        self.btn_add_parameter.connect(
            "clicked", self.__save_override, "param"
        )

        self.btn_response_go_back.connect("clicked", self.__go_back)
        self.btn_raw_go_back_body.connect("clicked", self.__go_back)
        self.btn_form_data_go_back_body.connect("clicked", self.__go_back)
        self.btn_edit_param_go_back.connect("clicked", self.__go_back)

        # General
        self.cookies = self.headers = self.auths = self.body = self.param = {}

        self.create_files_if_not_exists()
        self.__populate_overrides_list()
        self.raw_buffer = self.raw_source_view_body.get_buffer()
        self.response_buffer = self.response_source_view.get_buffer()
        self.response_source_view.props.editable = False

        # GSettings object
        self.settings = Gio.Settings.new("io.github.cleomenezesjr.GetOverHere")

    def set_needs_attention(self, *_args: tuple):
        # TODO make this function agnostic. get the swtich by self parent
        # TODO call this function when window open
        if not self.switch_cookie.get_state():
            self.cookies_page.set_needs_attention(True)
        else:
            self.cookies_page.set_needs_attention(False)

    def __on_send(self, *_args: tuple) -> None:
        """
        This function checks if the submitted URL is validself.

        If validated, it proceeds to generate the request,
        otherwise it returns a Toast informing that the URL
        is using bad/illegal format or that it is missing.
        """
        url = self.entry_url.get_text()
        method = self.entry_method.get_selected()
        body_type = self.form_data_toggle_button_body.props.active

        if not url:
            self.toast_overlay.add_toast(Adw.Toast.new(("Enter a URL")))
        else:
            if not is_valid_url(url):
                self.toast_overlay.add_toast(
                    Adw.Toast.new(
                        ("URL using bad/illegal format or missing URL")
                    )
                )
            else:
                body = self.__which_body_type(body_type)
                parameters = self.__which_parameter_type(url)
                cookies = (
                    self.cookies if self.switch_cookie.get_state() else None
                )
                headers = (
                    {value[0]: value[1] for key, value in self.headers.items()}
                    if self.switch_headers.get_state()
                    else None
                )
                which_method_thread = threading.Thread(
                    target=self.__which_method,
                    # TODO Remove parameters and use self variables
                    args=(method, url, body, cookies, headers),
                )
                which_method_thread.daemon = True
                which_method_thread.start()

                self.spinner.props.spinning = True
                self.leaflet.set_visible_child(self.response_page)
                self.response_stack.props.visible_child_name = "loading"

    def __which_parameter_type(self, url_entry: str) -> dict | None:
        if has_parameter(url_entry):
            separator = url_entry.find("?") + 1
            url_params = url_entry[separator:]
            per_param = (i.split("=") for i in url_params.split("&"))
            return {i[0]: i[1] for i in per_param}

        else:
            return self.param

    def __which_body_type(self, body_type: bool) -> dict | None:
        if body_type:
            body = self.body
        else:
            start, end = self.raw_buffer.get_bounds()
            raw_code = self.raw_buffer.get_text(start, end, True)
            if not len(raw_code) == 0:
                try:
                    body = json.loads(raw_code)
                except ValueError:
                    return self.toast_overlay.add_toast(
                        Adw.Toast.new(("Body must be in JSON format"))
                    )
            else:
                body = None

        return body

    def __which_method(
        self,
        method: int,
        url: str,
        body: dict | None,
        cookies: dict | None,
        headers: dict | None,
    ) -> Callable | None:
        try:
            method_list = {
                0: "get",
                1: "post",
                2: "put",
                3: "patch",
                4: "delete",
            }
            resolve_requests = ResolveRequests(
                url,
                self.session,
                cookies=cookies,
                headers=headers,
                body=body,
                parameters=self.param,
                authentication=[self.auth_type, self.auths],
            )
            get_resolve_requets_attr = getattr(
                resolve_requests, f"resolve_{method_list[method]}"
            )
            response, status_code, code_type = get_resolve_requets_attr()
        except exceptions.ConnectionError:
            self.leaflet.set_visible_child(self.home)
            return self.toast_overlay.add_toast(
                Adw.Toast.new(("Error: Couldn't resolve host name "))
            )

        # Dynamically change syntax highlight
        self._lm = SourceView()._lm
        language = self._lm.get_language(code_type)
        GLib.idle_add(self.response_buffer.set_language, language)

        # Setup response
        GLib.idle_add(self.response_buffer.set_text, response, -1)
        GLib.idle_add(self.response_page_header.set_subtitle, str(status_code))
        self.response_stack.props.visible_child_name = "response"

        # Clenup session
        self.session.cookies.clear()
        self.session.headers.clear()

    def __on_edit(self, *_args: tuple) -> None:
        if "body" in _args[1]:
            if not self.form_data_toggle_button_body.props.active:
                self.leaflet.set_visible_child(self.raw_page_body)
            else:
                self.leaflet.set_visible_child(self.form_data_page_body)
        if "param" in _args[1]:
            self.leaflet.set_visible_child(self.form_data_page_parameters)

    def __go_back(self, *_args: tuple) -> None:
        # TODO use actions instead
        self.leaflet.set_visible_child(self.home)

    @Gtk.Template.Callback()
    def update_subtitle_parameters(self, *_args) -> None:
        url_entry = self.entry_url.get_text()
        if has_parameter(url_entry):
            self.expander_row_parameters.set_enable_expansion(False)
            GLib.idle_add(self.expander_row_parameters.set_subtitle, "")
        else:
            self.expander_row_parameters.set_enable_expansion(True)
            parameters = [f"{i}={self.param[i]}" for i in self.param]
            GLib.idle_add(
                self.expander_row_parameters.set_subtitle,
                f"{'https://' if not url_entry else url_entry}"
                + f"?{html.escape('&').join(parameters)}",
            )

    def _show_cookie_dialog(self, widget, title, content=None):
        new_window = CookieDialog(
            parent_window=self, title=title, content=content
        )
        new_window.present()

    def _show_header_dialog(self, widget, title, content=None):
        new_window = HeaderDialog(
            parent_window=self, title=title, content=content
        )
        new_window.present()

    def _show_auth_dialog(self, widget, title, content=None):
        new_window = AuthDialog(
            parent_window=self, title=title, content=content
        )
        new_window.present()

    def create_files_if_not_exists(self) -> None:
        files = [COOKIES, BODY, PARAM, HEADERS, AUTHS]
        auths = {"Api Key": ["", "", "Header"], "Bearer Token": [""]}
        for file in files:
            if not os.path.exists(file):
                os.makedirs(os.path.dirname(file), exist_ok=True)
                with open(file, "w") as json_file:
                    json_file.write(
                        json.dumps(auths if "auths" in file else {})
                    )

    @Gtk.Template.Callback()
    def on_auth_entry_active(self, widget, args) -> None:
        auth_type = self.auth_type.props.selected_item.get_string()
        try:
            entry_content = getattr(self, args).get_text()
        except TypeError:
            if auth_type == "Api Key":
                entry_content = widget.props.selected_item.get_string()
                args = "api_key_auth_add_to"

        entries_position = {
            "Api Key": {
                "api_key_auth_key": 0,
                "api_key_auth_value": 1,
                "api_key_auth_add_to": 2,
            },
            "Bearer Token": {"bearer_token": 0},
        }

        # Insert Auth
        with open(AUTHS, "r+") as file:
            file_content = json.load(file)
            file_content[auth_type][
                entries_position[auth_type][args]
            ] = entry_content
            file.truncate(0)
            file.seek(0)
            json.dump(file_content, file, indent=2)

        self.auths[auth_type][
            entries_position[auth_type][args]
        ] = entry_content

    @Gtk.Template.Callback()
    def on_auth_type_changed(self, arg, kwargs):
        # TODO use this method on Method type
        type = self.auth_type.props.selected_item.get_string()
        self.bearer_token_prefs.props.visible = type == "Bearer Token"
        self.api_key_prefs.props.visible = type == "Api Key"

    def __save_override(self, *_args: tuple) -> None:
        """
        This function check if the override name is not empty, then
        store it in the configuration and add a new entry to
        the list. It also clears the entry field
        """
        match _args[1]:
            case "cookies":
                title: str = _args[2]
                subtitle: str = _args[3]
                id: str = _args[4]
                insertion_date = id or dt.today().isoformat()

                # Insert Cookie
                with open(COOKIES, "r+") as file:
                    file_content = json.load(file)
                    # Save Cookies
                    file_content[insertion_date] = [title, subtitle]
                    file.truncate(0)
                    file.seek(0)
                    json.dump(file_content, file, indent=2)

                    # Populate UI
                    _entry = PupulatorEntry(
                        window=self,
                        override=[
                            insertion_date,
                            [title, subtitle],
                        ],
                        content=COOKIES,
                    )
                    if not any(
                        [i == insertion_date for i in self.cookies.keys()]
                    ):
                        GLib.idle_add(
                            self.group_overrides_cookies.add,
                            _entry,
                        )
                        self.toast_overlay.add_toast(
                            Adw.Toast.new("Cookie created")
                        )
                    else:
                        self.toast_overlay.add_toast(
                            Adw.Toast.new("Cookie edited")
                        )

                self.cookies = file_content
                self.cookies_page.set_badge_number(len(file_content))

                # Clean up field
                self.group_overrides_cookies.set_description("")
            case "headers":
                title: str = _args[2]
                subtitle: str = _args[3]
                id: str = _args[4]
                insertion_date = id or dt.today().isoformat()

                # Insert Header
                with open(HEADERS, "r+") as file:
                    file_content = json.load(file)
                    # Save Header
                    file_content[insertion_date] = [title, subtitle]
                    file.truncate(0)
                    file.seek(0)
                    json.dump(file_content, file, indent=2)

                    # Populate UI
                    _entry = PupulatorEntry(
                        window=self,
                        override=[
                            insertion_date,
                            [title, subtitle],
                        ],
                        content=HEADERS,
                    )
                    if not any(
                        [i == insertion_date for i in self.headers.keys()]
                    ):
                        GLib.idle_add(self.group_overrides_headers.add, _entry)
                        self.toast_overlay.add_toast(
                            Adw.Toast.new("Header created")
                        )
                    else:
                        self.toast_overlay.add_toast(
                            Adw.Toast.new("Header edited")
                        )

                self.headers = file_content
                self.headers_page.set_badge_number(len(file_content))

                # Clean up field
                self.group_overrides_headers.set_description("")
            case "body":
                body_key = self.entry_body_key.get_text()
                body_value = self.entry_body_value.get_text()

                if body_key != "" and body_value != "":
                    with open(BODY, "r+") as file:
                        file_content = json.load(file)
                        if not any(
                            [i == body_key for i in file_content.keys()]
                        ):
                            # Save Body
                            file_content.update({body_key: body_value})
                            file.seek(0)
                            json.dump(file_content, file, indent=2)

                            # Populate UI
                            _entry = PupulatorEntry(
                                window=self,
                                override=[body_key, body_value],
                                content=BODY,
                            )
                            GLib.idle_add(
                                self.group_overrides_body.add, _entry
                            )
                        else:
                            return self.toast_overlay.add_toast(
                                Adw.Toast.new(("Key already exists"))
                            )

                    self.body = file_content
                    self.body_counter(file_content)

                    # Clean up fields
                    self.group_overrides_body.set_description("")
                    self.entry_body_key.set_text("")
                    self.entry_body_value.set_text("")
            case "param":
                param_key = self.entry_param_key.get_text()
                param_value = self.entry_param_value.get_text()

                if param_key != "" and param_value != "":
                    with open(PARAM, "r+") as file:
                        file_content = json.load(file)
                        if not any(
                            [i == param_key for i in file_content.keys()]
                        ):
                            # Save Parameters
                            file_content.update({param_key: param_value})
                            file.seek(0)
                            json.dump(file_content, file, indent=2)

                            # Populate UI
                            _entry = PupulatorEntry(
                                window=self,
                                override=[param_key, param_value],
                                content=PARAM,
                            )
                            GLib.idle_add(
                                self.group_overrides_param.add, _entry
                            )
                        else:
                            return self.toast_overlay.add_toast(
                                Adw.Toast.new(("Key already exists"))
                            )

                    self.param = file_content

                    # Clean up fields
                    self.group_overrides_param.set_description("")
                    self.entry_param_key.set_text("")
                    self.entry_param_value.set_text("")

    def __populate_overrides_list(self) -> None:
        # TODO populate url preview with parameters

        """
        This function populate rows from json files
        """
        files = {
            "cookie": [COOKIES, "cookies"],
            "body": [BODY, "body"],
            "parameter": [PARAM, "param"],
            "header": [HEADERS, "headers"],
            "authentication": [AUTHS, "auths"],
        }

        for file in files:
            with open(files[file][0], "r") as json_file:
                overrides = json.load(json_file)
                self.cookies = overrides if "cookie" in file else self.cookies
                self.body = overrides if "body" in file else self.body
                self.param = overrides if "parameter" in file else self.param
                self.headers = overrides if "header" in file else self.headers
                self.auths = (
                    overrides if "authentication" in file else self.auths
                )
                if file != "authentication":
                    if not bool(overrides):
                        getattr(
                            self, f"group_overrides_{files[file][1]}"
                        ).set_description((f"No {file} added."))
                    else:
                        getattr(
                            self, f"group_overrides_{files[file][1]}"
                        ).set_description("")
                        for override in overrides:
                            _entry = PupulatorEntry(
                                window=self,
                                override=[override, overrides[override]],
                                content=files[file][0],
                            )

                            GLib.idle_add(
                                getattr(
                                    self, f"group_overrides_{files[file][1]}"
                                ).add,
                                _entry,
                            )
                else:
                    PupulatorEntry(
                        window=self,
                        override=overrides,
                        content=files[file][0],
                    )

        # TODO set and change badge number when it has a change
        self.cookies_page.set_badge_number(len(self.cookies))
        self.headers_page.set_badge_number(len(self.headers))
        self.body_counter(self.body)

    def body_counter(self, overrides) -> None:
        """Body counter and its visibility"""
        counter_label = self.counter_label_form_data_body
        if len(overrides) > 0:
            if counter_label.get_visible() is False:
                counter_label.set_visible(True)
            counter_label.set_label(str(len(overrides)))
        else:
            counter_label.set_visible(False)
