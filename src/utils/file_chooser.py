from gi.repository import GLib, Gtk


class FileDialog:
    def __init__(self, window: "EscamboWindow", title: str):
        self.open_multiple_files(window, title)

    def open_multiple_files(self, escambo_window, title: str):
        dialog_for_multiple_files = Gtk.FileDialog(title=title)
        dialog_for_multiple_files.open_multiple(
            escambo_window, None, self.on_multiple_files_opened
        )

    def on_multiple_files_opened(self, dialog, result):
        files = dialog.open_multiple_finish(result)
        try:
            if files is not None:
                # files.load_contents_async(None, self.open_file_complete)
                for file in files:
                    print(file.get_path())
                # Handle loading file from here
        except GLib.Error as error:
            print(f"Error opening file: {error.message}")

    def open_file_complete(self, file, result):
        contents = file.load_contents_finish(result)
        if not contents[0]:
            path = file.peek_path()
            print(f"Unable to open {path}: {contents[1]}")
            return None

        try:
            text = contents[1].decode("utf-8")
            print(text)
        except UnicodeError as err:
            path = file.peek_path()
            print(
                f"Unable to load the contents of {path}: the file is not encoded with UTF-8"
            )
            return None
