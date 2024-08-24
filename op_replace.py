import bpy
import os
import csv
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator, Panel

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


class MIO3BONE_OT_ConvertByPreset(Operator):
    bl_idname = "mio3bone.convert_preset"
    bl_label = "Replace"
    bl_description = "Bone name to Humanoid format"
    bl_options = {"REGISTER", "UNDO"}

    type: bpy.props.EnumProperty(
        default="VROID_HUMANOID",
        items=[
            ("VROID_HUMANOID", "VRoid → UpperArm_L", ""),
            ("MMD_HUMANOID", "MMD → UpperArm_L", ""),
        ],
    )
    reversed: bpy.props.BoolProperty(name="reversed", default=False)
    full_convert: bpy.props.BoolProperty(name="all_convert", default=True)

    files = {"VROID_HUMANOID": "vroid.csv", "MMD_HUMANOID": "mmd.csv"}

    default_prefixes = ["J_Adj_", "J_Sec_", "J_Bip_"]

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE"

    def execute(self, context):
        file = os.path.join(TEMPLATE_DIR, self.files[self.type])
        with open(file) as f:
            reader = csv.reader(f)
            bone_pairs = list(reader)

        for pair in bone_pairs:
            if self.reversed:
                rename(pair[0], pair[1], context)
            else:
                rename(pair[1], pair[0], context)

        if self.full_convert and self.type == "VROID_HUMANOID" and not self.reversed:
            armature = context.active_object
            for bone in armature.pose.bones:
                original_name = bone.name
                new_name = original_name
                for prefix in self.default_prefixes:
                    if new_name.startswith(prefix):
                        new_name = new_name[len(prefix) :]
                        break
                if new_name != original_name:
                    bone.name = new_name
            bpy.ops.armature.convert_bone_names()

        return {"FINISHED"}


def rename(name_from, name_to, context):
    armature = context.active_object
    if armature.type != "ARMATURE":
        return

    bone = armature.data.bones.get(name_from)
    if bone:
        bone.name = name_to


def initShapeKey(context):
    if context.active_object.data.shape_keys is None:
        bpy.ops.object.shape_key_add(from_mix=False)


class MIO3BONE_PT_ConvertByPreset(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Mio3"
    bl_label = "Preset Convert"
    bl_parent_id = "MIO3BONE_PT_Main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.operator("mio3bone.convert_preset", text="VRoid → UpperArm_L").type = (
            "VROID_HUMANOID"
        )
        layout.operator("mio3bone.convert_preset", text="MMD → UpperArm_L").type = (
            "MMD_HUMANOID"
        )


classes = [MIO3BONE_OT_ConvertByPreset, MIO3BONE_PT_ConvertByPreset]


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
