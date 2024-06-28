import bpy
import re
from bpy.props import EnumProperty, PointerProperty, StringProperty, CollectionProperty
from bpy.types import Operator, Panel, PropertyGroup
from bpy.app.translations import pgettext


class MIO3BONE_PG_PrefixItem(PropertyGroup):
    prefix: StringProperty(name="Prefix")


class MIO3BONE_PG_PrefixList(PropertyGroup):
    items: CollectionProperty(name="items", type=MIO3BONE_PG_PrefixItem)
    active_index: bpy.props.IntProperty()


class MIO3BONE_Props(PropertyGroup):
    prefixs: bpy.props.PointerProperty(name="vglist", type=MIO3BONE_PG_PrefixList)
    input_prefix: bpy.props.StringProperty(name="Prefix", default="Twist_")
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

    conventions = {
        "UpperArm_L": {
            "separator": "",
            "side_format": "_{}",
            "side_type": "suffix",
        },
        "Upper Arm_L": {
            "separator": " ",
            "side_format": "_{}",
            "side_type": "suffix",
        },
        "Upper_Arm_L": {
            "separator": "_",
            "side_format": "_{}",
            "side_type": "suffix",
        },
        "UpperArm.L": {
            "separator": "",
            "side_format": ".{}",
            "side_type": "suffix",
        },
        "Upper Arm.L": {
            "separator": " ",
            "side_format": ".{}",
            "side_type": "suffix",
        },
        "Upper_Arm.L": {
            "separator": "_",
            "side_format": ".{}",
            "side_type": "suffix",
        },
        "L_UpperArm": {
            "separator": "",
            "side_format": "{}_",
            "side_type": "prefix",
        },
        "Generic": {
            "separator": "",
            "side_format": "{}",
            "side_type": "none",
        },
    }

    patterns = {
        "Right": {
            "pattern": r"(.+)[\._]([LR])(?:(\.\d+))?$",
        },
        "Left": {
            "pattern": r"^([LR])[\._](.+)(?:(\.\d+))?$",
        },
        "Generic": {
            "pattern": r"(.+?)(?:(\.\d+))?$",
        },
    }

    def detect_name_component(self, bone_name, prefixes):
        prefix = ""
        base = bone_name
        for p in prefixes:
            if bone_name.startswith(p):
                prefix = p
                base = bone_name[len(p) :]
        name, side, number = self.detect_pattern(base)
        return prefix, name, side, number

    def detect_pattern(self, name):
        for type, data in self.patterns.items():
            match = re.match(data["pattern"], name)
            if match:
                if type == "Right":
                    return match.group(1), match.group(2), match.group(3) or ""
                elif type == "Left":
                    return match.group(2), match.group(1), match.group(3) or ""
                else:
                    return match.group(1), "", match.group(2) or ""
        return name, "", ""

    def join_name_component(self, prefix, name, side, number, convert_type):
        conv_data = self.conventions[convert_type]
        if side == "":
            return "".join([name, number])
        elif self.conventions[convert_type]["side_type"] == "suffix":
            newstr = "".join(
                [prefix, name, conv_data["side_format"].format(side), number]
            )
        else:
            newstr = "".join(
                [prefix, conv_data["side_format"].format(side), name, number]
            )
        return newstr

    def convert_name(self, name, to_conv):
        words = re.findall(r"[A-Z][a-z]*|[a-z]+", name)
        separator = self.conventions[to_conv]["separator"]
        if self.conventions[to_conv]["separator"] == "":
            newstr = separator.join(word.capitalize() for word in words)
        else:
            newstr = separator.join(words)
        return newstr

    def execute(self, context):
        armature = context.active_object
        if armature.type != "ARMATURE":
            self.report({"ERROR"}, "アーマチュアを選択してください")
            return {"CANCELLED"}

        props = context.scene.mio3bone
        convert_type = props.convert_types
        prefixs = [item.prefix for item in context.scene.mio3bone.prefixs.items]

        for bone in armature.pose.bones:
            if not bone.bone.hide:
                prefix, name, side, number = self.detect_name_component(
                    bone.name, prefixs
                )
                name = self.convert_name(name, convert_type)
                new_name = self.join_name_component(
                    prefix, name, side, number, convert_type
                )
                if new_name != bone.name:
                    bone.name = new_name

        return {"FINISHED"}


class MIO3BONE_OT_PrefixAdd(bpy.types.Operator):
    bl_idname = "mio3bone.prefix_add"
    bl_label = "Add Item"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        list = context.scene.mio3bone.prefixs
        input_prefix = context.scene.mio3bone.input_prefix
        new_item = list.items.add()
        new_item.prefix = input_prefix
        return {"FINISHED"}


class MIO3BONE_OT_PrefixRemove(bpy.types.Operator):
    bl_idname = "mio3bone.prefix_remove"
    bl_label = "Remove Item"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        list = context.scene.mio3bone.prefixs
        list.items.remove(list.active_index)
        list.active_index = min(max(0, list.active_index - 1), len(list.items) - 1)
        return {"FINISHED"}


class MIO3BONE_PT_Main(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Mio3"
    bl_label = "Mio3 Bones"

    def draw(self, context):
        layout = self.layout
        props = context.scene.mio3bone
        layout.label(text="Name Converter")
        layout.prop(props, "convert_types")
        layout.operator("armature.convert_bone_names", text="Convert")

        layout.label(text="カスタムプレフィックス")

        prefixs = context.scene.mio3bone.prefixs
        row = layout.row(align=True)
        row.label(text="Prefix")
        row.scale_x = 2
        row.prop(context.scene.mio3bone, "input_prefix", text="")

        row = layout.row()
        row.template_list(
            "MIO3BONE_UL_PrefixList",
            "prefixs",
            prefixs,
            "items",
            prefixs,
            "active_index",
            rows=3,
        )

        col = row.column(align=True)
        col.operator(MIO3BONE_OT_PrefixAdd.bl_idname, icon="ADD", text="")
        col.operator(MIO3BONE_OT_PrefixRemove.bl_idname, icon="REMOVE", text="")


class MIO3BONE_UL_PrefixList(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        row = layout.row(align=True)
        row.label(text=f"{item.prefix}", icon="PINNED")


classes = (
    MIO3BONE_PG_PrefixItem,
    MIO3BONE_PG_PrefixList,
    MIO3BONE_Props,
    MIO3BONE_OT_ConvertNames,
    MIO3BONE_OT_PrefixAdd,
    MIO3BONE_OT_PrefixRemove,
    MIO3BONE_UL_PrefixList,
    MIO3BONE_PT_Main,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mio3bone = PointerProperty(type=MIO3BONE_Props)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.mio3bone
