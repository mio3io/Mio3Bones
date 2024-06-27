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
                "Upper Arm.L",
                "Upper Arm.L",
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
        ],
        default="UpperArm_L",
    )


class MIO3BONE_OT_ConvertNames(Operator):
    bl_idname = "armature.convert_bone_names"
    bl_label = "Convert Bone Names"
    bl_description = "ポーズモードで表示されているボーンの名前を変換します"
    bl_options = {"REGISTER", "UNDO"}

    conventions = {
        "UpperArm_L": {
            "pattern": r"([A-Z][a-z]*(?:[A-Z][a-z]*)*)_([LR])(\.\d+)?$",
            "join": "{}{}{}",
            "separator": "",
            "suffix": "_{}",
        },
        "Upper Arm.L": {
            "pattern": r"(.+)\s*\.([LR])(\.\d+)?$",
            "join": "{}{}{}",
            "separator": " ",
            "suffix": ".{}",
        },
        "Upper Arm_L": {
            "pattern": r"(.+)\s*_([LR])(\.\d+)?$",
            "join": "{}{}{}",
            "separator": " ",
            "suffix": "_{}",
        },
        "Upper_Arm_L": {
            "pattern": r"(.+)_([LR])(\.\d+)?$",
            "join": "{}{}{}",
            "separator": "_",
            "suffix": "_{}",
        },
    }

    def detect_convention(self, name):
        for conv, data in self.conventions.items():
            if re.match(data["pattern"], name):
                return conv
        return None

    def split_name_and_suffix(self, name, convention):
        pattern = self.conventions[convention]["pattern"]
        match = re.match(pattern, name)
        if match:
            return match.group(1), match.group(2), match.group(3) or ""
        return name, None, ""

    def join_name_and_suffix(self, name, suffix, number, convention):
        conv_data = self.conventions[convention]
        newstr = "".join([name, conv_data["suffix"].format(suffix), number])
        return newstr

    def convert_name(self, name, to_conv):
        words = re.findall(r"[A-Z][a-z]*|[a-z]+", name)
        name = name.rstrip()
        separator = self.conventions[to_conv]["separator"]
        if to_conv == "UpperArm_L":
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
        convert_types = props.convert_types

        for bone in armature.pose.bones:
            if not bone.bone.hide:
                from_conv = self.detect_convention(bone.name)
                if from_conv:
                    base_name, suffix, number = self.split_name_and_suffix(
                        bone.name, from_conv
                    )
                    converted_base = self.convert_name(base_name, convert_types)
                    new_name = self.join_name_and_suffix(
                        converted_base, suffix, number, convert_types
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
    bpy.types.WindowManager.mio3bone = PointerProperty(
        type=MIO3BONE_Props
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.mio3bone