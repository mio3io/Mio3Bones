import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, BoolProperty
from bpy.app.translations import pgettext

bl_info = {
    "name": "Mio3 Bones",
    "author": "mio",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Armature",
    "description": "Bone support",
    "category": "Armature",
}


def select_current_selection(armature):
    current_selection = [
        (bone.name, bone.select_head, bone.select_tail)
        for bone in armature.edit_bones
        if bone.select
    ]
    if armature.use_mirror_x:
        bpy.ops.armature.select_mirror(extend=True)
    return current_selection


def restore_current_selection(armature, current_selection):
    if armature.use_mirror_x:
        bpy.ops.armature.select_all(action="DESELECT")
        for bone_name, select_head, select_tail in current_selection:
            bone = armature.edit_bones[bone_name]
            bone.select = True
            bone.select_head = select_head
            bone.select_tail = select_tail


def split_bone_chains(selected_bones):
    bone_chains = []
    current_chain = []
    for bone in selected_bones:
        if not current_chain or current_chain[-1].tail == bone.head:
            current_chain.append(bone)
        else:
            bone_chains.append(current_chain)
            current_chain = [bone]

    if current_chain:
        bone_chains.append(current_chain)
    return bone_chains


class MIO3_OT_bone_evenly(Operator):
    bl_idname = "armature.mio3_bone_evenly"
    bl_label = "Evenly Bones"
    bl_description = "ボーンの長さを均等にする"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="EDIT")

        armature = context.object.data
        current_selection = select_current_selection(armature)

        selected_bones = context.selected_bones
        if selected_bones:
            bone_chains = split_bone_chains(selected_bones)
            for chain in bone_chains:
                self.evenly(chain)

        restore_current_selection(armature, current_selection)
        return {"FINISHED"}

    # 反復して調整
    def evenly(self, chain, iterations=3):
        original_positions = [(bone.head.copy(), bone.tail.copy()) for bone in chain]
        for _ in range(iterations):
            total_length = sum(
                (tail - head).length for head, tail in original_positions
            )
            equal_length = total_length / len(chain)

            sum_distances = [0.0]
            for head, tail in original_positions:
                sum_distances.append(sum_distances[-1] + (tail - head).length)

            target_distances = [i * equal_length for i in range(1, len(chain) + 1)]

            def interpolate_position(distance):
                for i in range(len(sum_distances) - 1):
                    if sum_distances[i] <= distance <= sum_distances[i + 1]:
                        t = (distance - sum_distances[i]) / (
                            sum_distances[i + 1] - sum_distances[i]
                        )
                        return original_positions[i][0].lerp(
                            original_positions[i][1], t
                        )
                return original_positions[-1][1]

            chain[0].head = original_positions[0][0]
            for i in range(1, len(chain)):
                chain[i - 1].tail = interpolate_position(target_distances[i - 1])
                chain[i].head = chain[i - 1].tail
            chain[-1].tail = original_positions[-1][1]


class MIO3_OT_bone_align(Operator):
    bl_idname = "armature.mio3_bone_align"
    bl_label = "Align Bones (child)"
    bl_description = "ボーンを整列する（先頭と末端のボーンを基準）"
    bl_options = {"REGISTER", "UNDO"}

    roll: BoolProperty(name="Unify roles", default=False)
    preserve_length: BoolProperty(name="Preserve Length Bone", default=False)

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="EDIT")

        armature = context.object.data
        current_selection = select_current_selection(armature)

        selected_bones = context.selected_bones
        if selected_bones:
            bone_chains = split_bone_chains(selected_bones)
            for chain in bone_chains:
                self.seiretu(chain)

        restore_current_selection(armature, current_selection)
        return {"FINISHED"}

    def seiretu(self, chain):
        head = chain[0].head
        tail = chain[-1].tail
        direction = (tail - head).normalized()
        roll = chain[0].roll
        total_distance = (tail - head).length

        if self.preserve_length:
            positions = [head]
            for bone in chain:
                positions.append(positions[-1] + direction * bone.length)
            for i, bone in enumerate(chain):
                bone.head = positions[i]
                bone.tail = positions[i + 1]
        else:
            length_ratios = [
                bone.length / sum(bone.length for bone in chain) for bone in chain
            ]
            current_length = 0
            for i, bone in enumerate(chain):
                bone_length = total_distance * length_ratios[i]
                bone.head = head + direction * current_length
                current_length += bone_length
                bone.tail = head + direction * current_length

        if self.roll:
            for bone in chain:
                bone.roll = roll


def sort_bones(bone, sorted_bones, renamed_bones, selected_bones):
    if bone not in renamed_bones and bone in selected_bones:
        sorted_bones.append(bone)
        renamed_bones.add(bone)
        for child in bone.children:
            sort_bones(child, sorted_bones, renamed_bones, selected_bones)


class MIO3_OT_bone_numbering(Operator):
    bl_idname = "armature.mio3_bone_numbering"
    bl_label = "Numbering Bones"
    bl_description = "Numbering Bone"
    bl_options = {"REGISTER", "UNDO"}

    delim: EnumProperty(
        name="Delim",
        default=".",
        items=[
            (".", "Dot (.)", ""),
            ("_", "Under Bar (_)", ""),
            (" ", "Space", ""),
        ],
    )

    endbone: BoolProperty(name="EndBone", default=False)
    suffix: BoolProperty(name="Suffix L/R", default=False)

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="EDIT")

        selected_bones = [bone for bone in context.selected_bones if bone.select]
        if selected_bones:
            bone_chains = split_bone_chains(selected_bones)
            for chain in bone_chains:
                self.rename_bone(chain)
        return {"FINISHED"}

    def rename_bone(self, chain):
        name = chain[0].name
        base_name = name
        suffix = ""
        if self.suffix and name.endswith(("_L", "_R", ".L", ".R")):
            suffix = name[-2:]
            base_name = name[:-2]

        sorted_bones = []
        renamed_bones = set()
        for bone in chain:
            if bone.parent not in chain:
                sort_bones(bone, sorted_bones, renamed_bones, set(chain))

        temp_names = {}
        for i, bone in enumerate(sorted_bones):
            temp_name = f"TEMP_mio3bones_{i:03d}_{bone.name}"
            temp_names[bone.name] = temp_name
            bone.name = temp_name

        for i, bone in enumerate(sorted_bones):
            original_name = list(temp_names.keys())[
                list(temp_names.values()).index(bone.name)
            ]
            if original_name != name:
                if self.endbone and i == len(sorted_bones) - 1:
                    bone.name = f"{base_name}{self.delim}end{suffix}"
                else:
                    bone.name = f"{base_name}{self.delim}{i:03d}{suffix}"
            else:
                bone.name = name


def menu(self, context):
    menu_transform(self, context)
    menu_name(self, context)


def menu_transform(self, context):
    self.layout.separator()
    self.layout.operator(
        MIO3_OT_bone_align.bl_idname, text=pgettext(MIO3_OT_bone_align.bl_label)
    )
    self.layout.operator(
        MIO3_OT_bone_evenly.bl_idname, text=pgettext(MIO3_OT_bone_evenly.bl_label)
    )


def menu_name(self, context):
    self.layout.separator()
    self.layout.operator(
        MIO3_OT_bone_numbering.bl_idname, text=pgettext(MIO3_OT_bone_numbering.bl_label)
    )


translation_dict = {
    "ja_JP": {
        ("*", "Suffix L/R"): "L/Rを接尾辞にする",
        ("*", "Delim"): "デリミタ",
        ("*", "EndBone"): "エンドボーン",
        ("*", "Evenly Bones"): "ボーンを均等",
        ("*", "Align Bones (child)"): "ボーンを整列（末端を基準）",
        ("*", "Numbering Bones"): "ボーンに通し番号をふる",
        ("*", "Unify roles"): "ロールを統一",
        ("*", "Preserve Length Bone"): "各ボーンの長さを維持",
    }
}


classes = [MIO3_OT_bone_evenly, MIO3_OT_bone_align, MIO3_OT_bone_numbering]


def register():
    bpy.app.translations.register(__name__, translation_dict)
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_transform_armature.append(menu_transform)
    bpy.types.VIEW3D_MT_edit_armature_names.append(menu_name)
    bpy.types.VIEW3D_MT_armature_context_menu.append(menu)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_transform_armature.remove(menu_transform)
    bpy.types.VIEW3D_MT_edit_armature_names.remove(menu_name)
    bpy.types.VIEW3D_MT_armature_context_menu.remove(menu)
    bpy.app.translations.unregister(__name__)


if __name__ == "__main__":
    register()
