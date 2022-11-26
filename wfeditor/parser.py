import json
from pathlib import Path
from random import randint

from PIL import Image

from component import Component
from decoder.watch_face import WatchFace
from widget_type import WidgetType

PARENT_FOLDER = Path(__file__).parent.resolve()


def index_images(folder):
    indexes = {}
    for image in Path(folder).iterdir():
        if image.suffix == ".png" and image.stem.isnumeric():
            indexes[int(image.stem)] = str(image)
    return indexes


class WFEditorParser:
    default_images_indexes = index_images(PARENT_FOLDER / "defaultimages")

    def __init__(self, src):
        self.images_indexes = index_images(src)
        self.watchface = None
        self.folder = Path(src)

        with open(self.folder / "watchface.json", "r") as f:
            self.data = json.loads(f.read())

        self.parse()

    def parse(self):
        t = WidgetType.from_string_attrs

        self.watchface = WatchFace()
        background = self.data.get("Background")
        self.add_component(background["Image"])

        time_data = self.data.get("Time")
        if time_data is not None:
            hours = time_data.get("Hours")
            minutes = time_data.get("Minutes")
            seconds = time_data.get("Seconds")

            self.add_component(hours, t("HOUR", "TIME", "FORMAT_DECIMAL_2_DIGITS", "NSS0"))
            self.add_component(minutes, t("MINUTE", "TIME", "FORMAT_DECIMAL_2_DIGITS", "NSS0"))
            self.add_component(seconds, t("SECOND", "TIME", "FORMAT_DECIMAL_2_DIGITS", "NSS0"))

        date_data = self.data.get("Date")
        if date_data is not None:
            weekday = date_data.get("WeekDay")
            self.add_component(weekday, t("DAY_OF_WEEK", "DAY", "FORMAT_IMAGE", "SS"))

            monthandday_data = date_data.get("MonthAndDay")
            if monthandday_data is not None:
                if "OneLine" in monthandday_data:
                    raise RuntimeError("OneLine MonthAndDay is not supported!")
                separate_data = monthandday_data.get("Separate")
                if separate_data is not None:
                    day = separate_data.get("Day")
                    month = separate_data.get("Month")

                    self.add_component(day, t("DAY_OF_MONTH", "DAY", "FORMAT_DECIMAL_2_DIGITS", "NSS0"))
                    self.add_component(month, t("MONTH", "DAY", "FORMAT_DECIMAL_2_DIGITS", "NSS0"))

        activity_data = self.data.get("Activity")
        if activity_data is not None:
            steps = activity_data.get("Steps")
            pulse = activity_data.get("Pulse")
            calories = activity_data.get("Calories")

            self.add_component(steps, t("NORMAL", "STEPS", "FORMAT_DECIMAL_5_DIGITS", "NSS"))
            self.add_component(pulse, t("NORMAL", "HEART_RATE", "FORMAT_DECIMAL_3_DIGITS", "NSS"))
            self.add_component(calories, t("NORMAL", "CALORIES", "FORMAT_DECIMAL_5_DIGITS", "NSS"))

        battery_data = self.data.get("Battery")
        if battery_data is not None:
            battery = battery_data.get("Text")

            self.add_component(battery, t("NORMAL", "BATTERY", "FORMAT_DECIMAL_3_DIGITS", "NSS"))

        self.watchface.preview = Component(Component.PREVIEW)
        self.watchface.preview.static_image = Image.open(self.folder / "preview.png")
        self.watchface.preview.resolve()

        self.watchface.name = "Unnamed"
        self.watchface.face_id = str(randint(1, 65130061))

    def add_component(self, component_data, widget_type=None):
        if component_data is not None:
            component = self.parse_component(component_data, widget_type)
            self.watchface.components.append(component)

    def parse_component(self, component_image, widget_type=None):
        if "Tens" in component_image:
            return self.parse_component(component_image["Tens"], widget_type)

        component = Component(Component.WIDGET)
        component.widget_type = widget_type
        image_index = int(component_image["ImageIndex"])
        if widget_type is None:
            component.static_image = self.load_image(image_index)
        else:
            images_count = int(component_image["ImagesCount"])
            component.images = []
            for i in range(images_count):
                component.images.append(self.load_image(image_index + i))

        alignment = component_image.get("Alignment")
        if alignment is not None and alignment != "TopLeft":
            raise RuntimeError("only TopLeft alignment is supported")
        x = component_image.get("X")
        if x is None: x = component_image.get("TopLeftX")
        y = component_image.get("Y")
        if y is None: y = component_image.get("TopLeftY")
        component.x = int(x) if x is not None else None
        component.y = int(y) if y is not None else None
        component.resolve()

        return component

    def load_image(self, index):
        if index in self.images_indexes:
            return Image.open(self.folder / self.images_indexes[index])
        elif index in self.default_images_indexes:
            return Image.open(PARENT_FOLDER / "defaultimages" / self.default_images_indexes[index])