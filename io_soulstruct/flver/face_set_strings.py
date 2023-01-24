import bmesh
import bpy
from bpy.props import StringProperty


# Holds bmesh instance for face set adjustment.
FACE_SET_BMESH = {}


def set_face_set_layer(self, context):
    """Face set update method."""
    eo = context.edit_object
    bm = FACE_SET_BMESH.setdefault(eo.name, bmesh.from_edit_mesh(eo.data))
    face = bm.faces.active
    face_set = bm.faces.layers.string.get("face_set")
    if face and face_set:
        for c in self.face_set_string:
            try:
                c = int(c)
            except ValueError:
                # TODO: operator report warning
                print(f"Non-integer character in face set string: {c}")
                return None
            face_set_count = context.view_layer.objects.active["Face Set Count"]
            if c >= face_set_count:
                # TODO: operator report warning
                print(f"Mesh has no face set with index {c}. Face set count is {face_set_count}.")
                return None
        face[face_set] = self.face_set_string.encode()
    return None


bpy.types.WindowManager.face_set_string = StringProperty(name="FLVER Face Set", update=set_face_set_layer)


def set_face_set_string(bm):
    """Keep wm.face_set_string updated to active face."""
    face = bm.faces.active
    if face is not None:
        face_set_layer = bm.faces.layers.string.get("face_set")
        if face_set_layer:
            bpy.context.window_manager.face_set_string = face[face_set_layer].decode()
    return None


def edit_object_change_handler(_):
    """Scene update handler."""
    obj = bpy.context.view_layer.objects.active
    if obj is None:
        return None
    # Add one instance of edit bmesh to global dictionary.
    if obj.mode == "EDIT" and obj.type == "MESH":
        bm = FACE_SET_BMESH.setdefault(obj.name, bmesh.from_edit_mesh(obj.data))
        set_face_set_string(bm)
        return None
    FACE_SET_BMESH.clear()
    return None


class FACE_SET_PT_main_panel(bpy.types.Panel):
    bl_label = "FLVER Face Sets"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"

    @classmethod
    def poll(cls, context):
        """Only allow in edit mode for a selected mesh with "Face Set Count" property."""
        return (
            context.mode == "EDIT_MESH"
            and context.object is not None
            and context.object.type == "MESH"
            and context.object.get("Face Set Count") is not None
        )

    def draw(self, context):
        obj = context.object
        bm = FACE_SET_BMESH.setdefault(obj.name, bmesh.from_edit_mesh(obj.data))
        face = bm.faces.active
        face_set_layer = bm.faces.layers.string.get("face_set")
        if face_set_layer is None:
            self.layout.row().label(text="No face sets.")
        elif face is None:
            self.layout.row().label(text="No face selected.")
        else:
            wm = context.window_manager
            self.layout.prop(wm, "face_set_string")
            row = self.layout.row()
            row.label(text="FLVER Face Sets")
            row.label(text=face[face_set_layer].decode())
