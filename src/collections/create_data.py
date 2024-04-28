import json
import os

from gi.repository import Gio, GLib

from .model import DataObject


def create_and_store_data(store: Gio.ListStore) -> dict | None:
    collections_folder: str = os.path.join(
        GLib.get_user_config_dir(), "collections"
    )
    try:
        collections_files_list: list = [
            coll
            for coll in os.listdir(collections_folder)
            if coll.endswith(".json")
        ]
    except FileNotFoundError:
        os.mkdir(collections_folder)
        return {}

    for file in collections_files_list:
        absolute_path: str = os.path.join(
            GLib.get_user_config_dir(), "collections", file
        )

        with open(absolute_path, "r+") as file:
            file_content: dict = json.load(file)

        if "info" not in file_content:
            # TODO: raise message
            return None

        info: dict = file_content["info"]

        # TODO: set id based on escambo or postman id
        id: str = "id" in info and info["id"] or ""
        if "_postman_id" in info:
            id = info["_postman_id"]

        collection_name: str = file_content["info"]["name"]
        _process_json(
            file_content["item"], collection := [], [collection_name]
        )
        store.append(DataObject(collection_name, children=collection))

    return {"collections_filenames": collections_files_list}


def _process_json(data: list, collection: list, path: list) -> list:
    for i, item in enumerate(data):
        current_path = path + [i]

        data_args: dict = {"txt": item.get("name", ""), "path": current_path}

        if "item" in item and isinstance(item["item"], list):
            data_args.update(
                {
                    "is_folder": True,
                    "children": _process_json(item["item"], [], current_path),
                }
            )
        if "request" in item:
            data_args["method"] = item["request"].get("method", "")

        collection.append(DataObject(**data_args))
    return collection
