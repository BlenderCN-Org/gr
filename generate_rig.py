# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any laTter version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


##########################################################################################################
##########################################################################################################

import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import *
from mathutils import Vector

from .constants import Constants
from .m_base import prepare
from .m_base import finalize
from .m_base import root_bone
from .m_base import ik_prop_bone
from .m_biped_torso import biped_torso
from .m_biped_arm import biped_arm


class Op_GYAZ_GameRig_GenerateRig(bpy.types.Operator):
    bl_idname = "object.gyaz_game_rigger_generate_rig"
    bl_label = "GYAZ Game Rigger: Generate Rig"
    bl_description = ""

    generate__facial_rig: EnumProperty(
        name='Facial Rig',
        items=(
            ('NONE', 'NONE', ''),
            ('EYES', 'EYES', ''),
            ('EYES+JAW', 'EYES+JAW', ''),
            ('FULL', 'FULL', '')
        ),
        default='FULL')

    generate__fingers: BoolProperty(default=True, name='Fingers')

    generate__spring_belly: BoolProperty(default=True, name='Spring Belly')

    generate__spring_bottom: BoolProperty(default=True, name='Spring Bottom')

    generate__spring_chest: BoolProperty(default=True, name='Spring Chest')

    generate__twist_upperarm_count: EnumProperty(name='Twist Upperarm',
                                                 items=(('0', '0', ''), ('1', '1', ''), ('2', '2', ''), ('3', '3', '')),
                                                 default='3')

    generate__twist_forearm_count: EnumProperty(name='Twist Forearm',
                                                items=(('0', '0', ''), ('1', '1', ''), ('2', '2', ''), ('3', '3', '')),
                                                default='3')

    generate__twist_thigh_count: EnumProperty(name='Twist Thigh',
                                              items=(('0', '0', ''), ('1', '1', ''), ('2', '2', ''), ('3', '3', '')),
                                              default='3')

    generate__twist_shin_count: EnumProperty(name='Twist Shin',
                                             items=(('0', '0', ''), ('1', '1', ''), ('2', '2', ''), ('3', '3', '')),
                                             default='1')

    generate__twist_neck: BoolProperty(default=True, name='Twist Neck')

    def draw(self, context):
        lay = self.layout
        lay.prop(self, 'generate__fingers')
        lay.label(text='Twist Bones:')
        row = lay.row(align=True)
        row.label(text='Upperarm:')
        row.prop(self, 'generate__twist_upperarm_count', expand=True)
        row = lay.row(align=True)
        row.label(text='Forearm:')
        row.prop(self, 'generate__twist_forearm_count', expand=True)
        row = lay.row(align=True)
        row.label(text='Thigh:')
        row.prop(self, 'generate__twist_thigh_count', expand=True)
        row = lay.row(align=True)
        row.label(text='Shin:')
        row.prop(self, 'generate__twist_shin_count', expand=True)
        lay.prop(self, 'generate__twist_neck')
        lay.label(text='Spring Bones:')
        lay.prop(self, 'generate__spring_belly')
        lay.prop(self, 'generate__spring_bottom')
        lay.prop(self, 'generate__spring_chest')
        lay.label(text='Facial Rig:')
        lay.prop(self, 'generate__facial_rig', expand=True)
        lay.separator()

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    # operator function
    def execute(self, context):

        def main():

            generate__facial_rig = self.generate__facial_rig

            if generate__facial_rig == 'NONE':
                generate__face_eyes = False
                generate__face_jaw = False
                generate__face_detail = False

            elif generate__facial_rig == 'EYES':
                generate__face_eyes = True
                generate__face_jaw = False
                generate__face_detail = False

            elif generate__facial_rig == 'EYES+JAW':
                generate__face_eyes = True
                generate__face_jaw = True
                generate__face_detail = False

            elif generate__facial_rig == 'FULL':
                generate__face_eyes = True
                generate__face_jaw = True
                generate__face_detail = True

            generate__fingers = self.generate__fingers
            generate__spring_belly = self.generate__spring_belly
            generate__spring_bottom = self.generate__spring_bottom
            generate__spring_chest = self.generate__spring_chest
            generate__twist_upperarm_count = int(self.generate__twist_upperarm_count)
            generate__twist_forearm_count = int(self.generate__twist_forearm_count)
            generate__twist_thigh_count = int(self.generate__twist_thigh_count)
            generate__twist_shin_count = int(self.generate__twist_shin_count)
            generate__twist_neck = self.generate__twist_neck
            
            ####################################################################################################
            ####################################################################################################
            
            bvh_tree, shape_collection, merged_character_mesh = prepare()
            
            root_bone(shape_collection
                      )
            biped_torso(bvh_tree,
                        shape_collection,
                        module='spine', 
                        chain=('hips', 'spine_1', 'spine_2', 'spine_3'), 
                        first_parent_name='root_extract'
                        )
            ik_prop_bone(bvh_tree,
                         shape_collection,
                         name='ik_hand_prop', 
                         source_bone_name='hand_r', 
                         parent_name='root_extract'
                         )
            for side in Constants.sides:
                biped_arm(bvh_tree, 
                          shape_collection, 
                          module='arm' + side, 
                          chain=('shoulder' + side, 'upperarm' + side, 'forearm' + side, 'hand' + side), 
                          first_parent_name='spine_3', 
                          pole_target_name='elbow' + side, 
                          forearm_bend_back_limit=30, 
                          ik_hand_parent_name='ik_hand_prop', 
                          pole_target_parent_name='root_extract',
                          side=side,
                          upperarm_twist_count=generate__twist_upperarm_count, 
                          forearm_twist_count=generate__twist_forearm_count
                          )
                
            finalize(merged_character_mesh=merged_character_mesh)
            



        # safety checks
        obj = bpy.context.object

        good_to_go = False
        if obj.type == 'ARMATURE' and "GYAZ_rig" in obj.data:
            good_to_go = True

        if good_to_go == False:
            report(self, 'Object is not a GYAZ rig', 'WARNING')
        else:

            mesh_children = []
            for child in obj.children:
                if child.type == 'MESH':
                    mesh_children.append(child)

            if len(mesh_children) == 0:
                report(self, 'Object has no mesh children.', 'WARNING')

            else:

                if obj.scale != Vector((1, 1, 1)):
                    report(self, "Armature has object scaling, cannot proceed.", 'WARNING')

                else:
                    main()

        return {'FINISHED'}


#######################################################
#######################################################

# REGISTER

def register():
    bpy.utils.register_class(Op_GYAZ_GameRig_GenerateRig)


def unregister():
    bpy.utils.unregister_class(Op_GYAZ_GameRig_GenerateRig)


if __name__ == "__main__":
    register()