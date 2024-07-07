import bpy
import re
from bpy.props import (
    BoolProperty,
    IntProperty,
    StringProperty,
    EnumProperty,
    PointerProperty,
    CollectionProperty,
)
from bpy.types import Operator, Panel, PropertyGroup
from bpy.app.translations import pgettext


class MIO3BONE_PG_PrefixItem(PropertyGroup):
    prefix: StringProperty(name="Prefix")


class MIO3BONE_PG_PrefixList(PropertyGroup):
    items: CollectionProperty(name="items", type=MIO3BONE_PG_PrefixItem)
    active_index: IntProperty()


class MIO3BONE_Props(PropertyGroup):
    side_long: BoolProperty(name="Side Long", default=False)
    remove_prefix: BoolProperty(name="Remove", default=False)
    prefixs: PointerProperty(name="Prefix", type=MIO3BONE_PG_PrefixList)
    input_prefix: StringProperty(name="Prefix", default="Twist_")
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

    patterns = (
        {
            "pattern": r"(.+)[\._](L|R|Left|Right)(?:(\.\d+))?$",
            "side_type": "suffix",
        },
        {
            "pattern": r"^(L|R|Left|Right)[\._](.+)(?:(\.\d+))?$",
            "side_type": "prefix",
        },
        {
            "pattern": r"(.+)(Left|Right)(?:(\.\d+))?$",
            "side_type": "suffix",
        },
        {
            "pattern": r"^(Left|Right)([^a-z].*)(?:(\.\d+))?$",
            "side_type": "prefix",
        },
        {
            "pattern": r"(.+?)(?:(\.\d+))?$",
            "side_type": "none",
        },
    )

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
        for data in self.patterns:
            match = re.match(data["pattern"], name)
            if match:
                if data["side_type"] == "suffix":
                    return match.group(1), match.group(2), match.group(3) or ""
                elif data["side_type"] == "prefix":
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
        if re.match(r"^[a-zA-Z0-9\s_.\-]+$", name):
            words = re.findall(r"[A-Z][a-z]*|[a-z]+", name)
        else:
            words = [name]
        separator = self.conventions[to_conv]["separator"]
        if self.conventions[to_conv]["separator"] == "":
            newstr = separator.join(word.capitalize() for word in words)
        else:
            newstr = separator.join(words)
        return newstr

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE"

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
                if context.scene.mio3bone.remove_prefix:
                    prefix = ""

                if context.scene.mio3bone.side_long:
                    side = "Left" if side == "L" else side
                    side = "Right" if side == "R" else side
                else:
                    side = side[0] if side in ["Left", "Right"] else side

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


class MIO3BONE_PT_Convert(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Mio3"
    bl_label = "Format Convert"
    bl_parent_id = "MIO3BONE_PT_Main"

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

        layout.row().prop(context.scene.mio3bone, "remove_prefix", text="Remove Prefix")
        layout.row().prop(context.scene.mio3bone, "side_long", text="L/R -> Left/Right")


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
    MIO3BONE_PT_Convert,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mio3bone = PointerProperty(type=MIO3BONE_Props)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.mio3bone
