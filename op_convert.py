import bpy
import re
from bpy.props import EnumProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup
from bpy.app.translations import pgettext


class MIO3BONE_Props(PropertyGroup):
    convert_types: EnumProperty(
        name="After Format",
        description="",
        items=[
            (
                "UpperArm_L",
                "UpperArm_L (オススメ)",
                "",
            ),
            (
                "Upper Arm_L",
                "Upper Arm_L",
                "",
            ),
            (
                "Upper_Arm_L",
                "Upper_Arm_L",
                "",
            ),
            (
                "UpperArm.L",
                "UpperArm.L",
                "",
            ),
            (
                "Upper Arm.L",
                "Upper Arm.L",
                "",
            ),
            (
                "Upper_Arm.L",
                "Upper_Arm.L",
                "",
            ),
        ],
        default="UpperArm_L",
    )


class MIO3BONE_OT_ConvertNames(Operator):
    bl_idname = "armature.convert_bone_names"
    bl_label = "Convert Bone Names"
    bl_description = "ポーズモードで表示されているボーンの名前を変換します"
    bl_options = {"REGISTER", "UNDO"}

    patterns = {
        "UpperArm_L": {
            "pattern": r"([A-Z][a-z]*(?:[A-Z][a-z]*)*)_([LR])(\.\d+)?$",
            "separator": "",
            "side_format": "_{}",
            "side_type": "suffix",
        },
        "Upper Arm_L": {
            "pattern": r"(.+)\s*_([LR])(?:(\.\d+))?$",
            "separator": " ",
            "side_format": "_{}",
            "side_type": "suffix",
        },
        "Upper_Arm_L": {
            "pattern": r"(.+)_([LR])(?:(\.\d+))?$",
            "separator": "_",
            "side_format": "_{}",
            "side_type": "suffix",
        },
        "UpperArm.L": {
            "pattern": r"([A-Z][a-z]*(?:[A-Z][a-z]*)*)\.([LR])(\.\d+)?$",
            "separator": "",
            "side_format": ".{}",
            "side_type": "suffix",
        },
        "Upper Arm.L": {
            "pattern": r"(.+)\s*\.([LR])(?:(\.\d+))?$",
            "separator": " ",
            "side_format": ".{}",
            "side_type": "suffix",
        },
        "Upper_Arm.L": {
            "pattern": r"(.+)\.([LR])(?:(\.\d+))?$",
            "separator": "_",
            "side_format": ".{}",
            "side_type": "suffix",
        },
        "L_UpperArm": {
            "pattern": r"([LR])_([^.]+)(\.\d+)?$",
            "separator": "",
            "side_format": "{}_",
            "side_type": "prefix",
        },
        "Generic": {
            "pattern": r"(.+?)(?:(\.\d+))?$",
            "separator": "",
            "side_format": "{}",
            "side_type": "none",
        },
    }

    prefixes = []

    __prefix = ""
    __body = ""
    __side = ""
    __number = ""

    def detect_prefix(self, name):
        self.__prefix = ""
        for prefix in self.prefixes:
            if name.startswith(prefix):
                self.__prefix = prefix
                self.__body = name[len(prefix) :]
                return self.__body
        self.__body = name
        return name

    def detect_convention(self, name):
        for conv, data in self.patterns.items():
            if re.match(data["pattern"], name):
                return conv
        return "Generic"

    def split_name_and_side(self, name, convert_type):
        pattern = self.patterns[convert_type]["pattern"]
        match = re.match(pattern, name)
        if match:
            if self.patterns[convert_type]["side_type"] == "suffix":
                return match.group(1), match.group(2), match.group(3) or ""
            elif self.patterns[convert_type]["side_type"] == "prefix":
                return match.group(2), match.group(1), match.group(3) or ""
            else:
                return match.group(1), "", match.group(2) or ""
        return name, "", ""

    def join_name_and_side(self, name, side, number, convert_type, from_pattern):
        conv_data = self.patterns[convert_type]
        if from_pattern == "Generic":
            return "".join([name, number])
        elif self.patterns[convert_type]["side_type"] == "suffix":
            newstr = "".join([self.__prefix, name, conv_data["side_format"].format(side), number])
        else:
            newstr = "".join([self.__prefix, conv_data["side_format"].format(side), name, number])

        return newstr

    def convert_name(self, name, to_conv):
        words = re.findall(r"[A-Z][a-z]*|[a-z]+", name)
        name = name.rstrip()
        separator = self.patterns[to_conv]["separator"]
        if self.patterns[to_conv]["separator"] == "":
            newstr = separator.join(word.capitalize() for word in words)
        else:
            newstr = separator.join(words)
        return newstr

    def execute(self, context):
        armature = context.active_object
        if armature.type != "ARMATURE":
            self.report({"ERROR"}, "アーマチュアを選択してください")
            return {"CANCELLED"}

        props = context.window_manager.mio3bone
        convert_type = props.convert_types

        for bone in armature.pose.bones:
            if not bone.bone.hide:

                name = self.detect_prefix(bone.name)
                from_pattern = self.detect_convention(name)
                if from_pattern:
                    base_name, side, number = self.split_name_and_side(
                        name, from_pattern
                    )
                    converted_base = self.convert_name(base_name, convert_type)
                    new_name = self.join_name_and_side(
                        converted_base, side, number, convert_type, from_pattern
                    )
                    if new_name != bone.name:
                        bone.name = new_name

        return {"FINISHED"}


class MIO3BONE_PT_Main(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Mio3"
    bl_label = "Mio3 Bones"

    def draw(self, context):
        layout = self.layout
        props = context.window_manager.mio3bone
        layout.label(text="Name Converter")
        layout.prop(props, "convert_types")
        layout.operator("armature.convert_bone_names", text="Convert")


classes = (
    MIO3BONE_Props,
    MIO3BONE_OT_ConvertNames,
    MIO3BONE_PT_Main,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.mio3bone = PointerProperty(type=MIO3BONE_Props)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.mio3bone
