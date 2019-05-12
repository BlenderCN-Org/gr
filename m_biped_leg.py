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

from .constants import Constants
from .utils import create_module_prop_bone
from .utils import bone_settings
from .utils import duplicate_bone
from .utils import get_distance
from .utils import set_parent_chain
from .utils import prop_to_drive_constraint
from .utils import mirror_bone_to_point
from .utils import bone_visibility
from .utils import set_module_on_relevant_bones
from .utils import three_bone_limb
from .utils import isolate_rotation


def biped_leg(module, chain, pole_target, parent_pt_to_ik_target, shin_bend_axis, shin_bend_back, ik_parent, foot_toes_bend_axis, pole_parent, side):

    ik_group = set_ik_group(side)

    # chain length should be exactly 4

    # bones that should be used for animation
    relevant_bones = []

    # bone that holds all properties of the module
    prop_bone_name = create_mudule_prop_bone(module=module)

    # set parent
    first_parent = get_parent(chain[0])

    # LOW-LEVEL BONES
    # set parents
    for index, name in enumerate(chain):
        bpy.ops.object.mode_set(mode='EDIT')
        ebones = rig.data.edit_bones
        if index == 0:
            ebones[name].parent = ebones[first_parent]
        else:
            ebones[name].parent = ebones[chain[index - 1]]

        relevant_bones.append(name)
        bone_settings(name=name, layer=base_layer, group=base_group, deform=True, lock_loc=True,
                      lock_rot=False, lock_scale=True, type='base')

    # _____________________________________________________________________________________________________

    # three bone limb set-up
    three_bone_limb(module=module, b1=chain[0], b2=chain[1], b3=chain[2], pole_target=pole_target,
                    pt_distance=pole_target_distance, parent_pt_to_ik_target=parent_pt_to_ik_target,
                    b2_bend_axis=shin_bend_axis, b2_bend_back=shin_bend_back, first_parent=first_parent,
                    fk_layer=fk_layer, ctrl_ik_layer=ctrl_ik_layer, ik_group=ik_group,
                    keep_last_bone_rot_when_radius_check=False, ik_parent=ik_parent,
                    pole_parent=pole_parent, b3_shape_bone='UP')

    isolate_rotation(module=module, parent_bone=first_parent, first_bone=fk_prefix + chain[0])

    # TOES BONE:
    # FK
    name = fk_prefix + chain[3]
    duplicate_bone(source_name=chain[3], new_name=name, parent_name=fk_prefix + chain[2],
                   roll_override=False, length_override=None)
    bone_settings(name=name, layer=fk_layer, group='fk', deform=False, lock_loc=True, lock_rot=False,
                  lock_scale=True, type='fk')
    set_bone_shape(bone_name=name, shape='sphere', transform_bone=None, auto_scale_with_offset=False,
                   manual_scale=target_shape_size, shape_bone=None, keep_rot_when_radius_check=False,
                   use_bone_size=False, shape_bone_parent_override=False)
    relevant_bones.append(name)

    # bind low-level bones to FK constraints
    bpy.ops.object.mode_set(mode='POSE')
    pbone = rig.pose.bones[chain[3]]

    c = pbone.constraints.new('COPY_ROTATION')
    c.name = 'bind_to_fk_1'
    c.target = rig
    c.subtarget = fk_prefix + chain[3]
    c.mute = True

    # lock toe axes
    bend_axis = foot_toes_bend_axis
    if 'X' in bend_axis:
        lock_1 = 1
        lock_2 = 2

    for ai in [lock_1, lock_2]:
        prop_to_drive_pbone_attribute_with_array_index(name, bone_name=name,
                                                       prop_name='limit_fk_toes' + side,
                                                       attribute='lock_rotation', array_index=ai,
                                                       prop_min=0, prop_max=1, prop_default=0,
                                                       description='limit toes to single axis rotation',
                                                       expression='v1')

    # filler bones (needed for GYAZ retargeter)
    bpy.ops.object.mode_set(mode='EDIT')
    ebone = rig.data.edit_bones.new(name='fk_filler_' + chain[0])
    ebones = rig.data.edit_bones
    ebone.head = ebones[first_parent].head
    ebone.tail = ebones[chain[0]].head
    ebone.roll = 0
    ebone.parent = ebones[first_parent]
    set_bone_only_layer(bone_name=ebone.name, layer_index=fk_extra_layer)

    # IK
    name = ik_prefix + chain[3]
    duplicate_bone(source_name=chain[3], new_name=name, parent_name=ik_prefix + chain[2],
                   roll_override=False, length_override=None)
    bone_settings(name=name, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=True,
                  lock_rot=False, lock_scale=True, type='ik')
    set_bone_shape(bone_name=name, shape='cube', transform_bone=None, auto_scale_with_offset=False,
                   manual_scale=target_shape_size, shape_bone=None, keep_rot_when_radius_check=False,
                   use_bone_size=False, shape_bone_parent_override=False)
    relevant_bones.append(name)

    # lock toe axes
    bend_axis = foot_toes_bend_axis
    if 'X' in bend_axis:
        lock_1 = 1
        lock_2 = 2

    for ai in [lock_1, lock_2]:
        prop_to_drive_pbone_attribute_with_array_index(name, bone_name=name,
                                                       prop_name='limit_ik_toes' + side,
                                                       attribute='lock_rotation', array_index=ai,
                                                       prop_min=0, prop_max=1, prop_default=1,
                                                       description='limit toes to single axis rotation',
                                                       expression='v1')

    # bind low-level bones to IK constraints
    bpy.ops.object.mode_set(mode='POSE')
    pbone = rig.pose.bones[chain[3]]

    c = pbone.constraints.new('COPY_ROTATION')
    c.name = 'bind_to_ik_1'
    c.target = rig
    c.subtarget = ik_prefix + chain[3]
    c.mute = True

    # BIND TO (0: FK, 1: IK, 2:BIND)
    prop_to_drive_constraint(prop_bone_name, bone_name=chain[3], constraint_name='bind_to_fk_1',
                             prop_name='switch_' + module, attribute='mute', prop_min=0, prop_max=2,
                             prop_default=0, description='0:fk, 1:ik, 2:base', expression='1 - (v1 < 1)')
    prop_to_drive_constraint(prop_bone_name, bone_name=chain[3], constraint_name='bind_to_ik_1',
                             prop_name='switch_' + module, attribute='mute', prop_min=0, prop_max=2,
                             prop_default=0, description='0:fk, 1:ik, 2:base',
                             expression='1 - (v1 > 0 and v1 < 2)')

    # SNAP INFO
    bpy.ops.object.mode_set(mode='POSE')
    pbone = rig.pose.bones[prop_bone_name]
    pbone['snapinfo_singlebone_0'] = [fk_prefix + chain[3], ik_prefix + chain[3]]

    # FOOT ROLL:
    # get heel position
    foot = chain[2]
    toes = chain[3]
    bpy.ops.object.mode_set(mode='EDIT')

    # set ray start and direction
    ray_start = rig.data.edit_bones[toes].head
    ray_direction = (0, 1, 0)
    ray_distance = 1

    # cast ray
    hit_loc, hit_nor, hit_index, hit_dist = my_tree.ray_cast(ray_start, ray_direction, ray_distance)

    # third-point of toes.head and hit_loc(heel)
    difference = ray_start - hit_loc
    difference /= 3
    third_point = hit_loc + difference

    # ik foot main
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = rig.data.edit_bones
    ik_foot_main = ik_prefix + 'main_' + foot
    ebone = ebones.new(name=ik_foot_main)
    ik_foot_name = ik_prefix + foot
    ik_foot_ebone = ebones[ik_foot_name]
    foot_length = get_distance(ik_foot_ebone.head, ik_foot_ebone.tail)
    ebone.head = ik_foot_ebone.head
    ebone.tail = (ik_foot_ebone.head[0], ik_foot_ebone.head[1] - foot_length, ik_foot_ebone.head[2])
    ebone.roll = radians(-180) if side == '_l' else radians(180)
    ebone.parent = ebones[ik_parent]
    bone_settings(name=ik_foot_main, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=False,
                  lock_rot=False, lock_scale=True, type='ik')
    set_bone_shape(bone_name=ik_foot_main, shape='cube', transform_bone=None,
                   auto_scale_with_offset=auto_bone_shape_scale_offset_limb, manual_scale=1,
                   shape_bone='UP', keep_rot_when_radius_check=False, use_bone_size=False,
                   shape_bone_parent_override=False)
    relevant_bones.append(ik_foot_main)

    # ik foot snap target
    snap_target_foot = 'snap_target_' + foot
    duplicate_bone(source_name=ik_foot_main, new_name=snap_target_foot, parent_name=fk_prefix + foot,
                   roll_override=False, length_override=False)
    bone_settings(name=snap_target_foot, layer=fk_extra_layer, group=None, deform=False, lock_loc=True,
                  lock_rot=True, lock_scale=True, type=None)

    # foot roll back
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = rig.data.edit_bones
    foot_roll_back = 'roll_back_' + foot
    ebone = ebones.new(name=foot_roll_back)
    ebone.head = hit_loc
    ebone.tail = third_point
    ebone.roll = ebones[foot].roll
    ebone.parent = ebones[ik_foot_main]
    bone_settings(name=foot_roll_back, layer=ctrl_ik_extra_layer, group=ik_group, deform=False,
                  lock_loc=True, lock_rot=False, lock_scale=True, type=None)

    # foot roll front
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = rig.data.edit_bones
    foot_roll_front = 'roll_front_' + foot
    ebone = ebones.new(name=foot_roll_front)
    ebone.head = ebones[toes].head
    ebone.tail = third_point
    ebone.roll = ebones[foot].roll
    ebone.parent = ebones[foot_roll_back]
    ebones[ik_prefix + foot].parent = ebones[foot_roll_front]
    bone_settings(name=foot_roll_front, layer=ctrl_ik_extra_layer, group=ik_group, deform=False,
                  lock_loc=True, lock_rot=False, lock_scale=True, type=None)

    # foot roll main
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = rig.data.edit_bones
    foot_roll_main = 'roll_main_' + foot
    ebone = ebones.new(name=foot_roll_main)
    ebone.head = ebones[foot].head
    length = get_distance(ebones[foot].head, ebones[foot].tail)
    ebone.tail = ebone.head + Vector((0, length, 0))
    ebone.roll = ebones[foot].roll
    ebone.parent = ebones[ik_foot_main]
    bone_settings(name=foot_roll_main, layer=ctrl_ik_layer, group=ik_group, deform=False, lock_loc=True,
                  lock_rot=False, lock_scale=True, type='ik')
    set_bone_shape(bone_name=foot_roll_main, shape='foot_roll', transform_bone=None,
                   auto_scale_with_offset=None, manual_scale=target_shape_size, shape_bone='LEAF',
                   keep_rot_when_radius_check=True, use_bone_size=False, shape_bone_parent_override=False)
    relevant_bones.append(foot_roll_main)

    # parent pole target to foot_roll_main
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = rig.data.edit_bones
    ebones['target_' + pole_target].parent = ebones[ik_foot_main]

    # ik_toes parent
    ik_toes_parent = ik_prefix + 'parent_' + toes
    duplicate_bone(source_name=ik_prefix + toes, new_name=ik_toes_parent, parent_name=ik_prefix + foot,
                   roll_override=False, length_override=None)
    bone_settings(name=ik_toes_parent, layer=ctrl_ik_extra_layer, group=None, deform=False, lock_loc=True,
                  lock_rot=False, lock_scale=True, type=None)
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = rig.data.edit_bones
    ebones[ik_prefix + toes].parent = ebones[ik_toes_parent]

    # relegate old ik_foot bone
    set_bone_only_layer(bone_name=ik_prefix + foot, layer_index=ctrl_ik_extra_layer)
    # update snap_info
    bpy.ops.object.mode_set(mode='POSE')
    pbones = rig.pose.bones
    old_snap_info = pbones['module_props__' + module]["snapinfo_3bonelimb_0"]
    old_snap_info[9], old_snap_info[10], old_snap_info[11] = snap_target_foot, ik_foot_main, foot_roll_main
    pbones['module_props__' + module]["snapinfo_3bonelimb_0"] = old_snap_info

    bpy.ops.object.mode_set(mode='POSE')
    pbones = rig.pose.bones
    # foot roll constraints:
    # foot roll front
    if foot_toes_bend_axis == '-X':
        use_x = True
        use_z = False

    pbone = pbones[foot_roll_front]
    c = pbone.constraints.new('COPY_ROTATION')
    c.name = 'copy foot_roll_main'
    c.target = rig
    c.subtarget = foot_roll_main
    c.use_x = use_x
    c.use_y = False
    c.use_z = use_z
    c.invert_x = False
    c.invert_y = False
    c.invert_z = False
    c.use_offset = False
    c.target_space = 'LOCAL'
    c.owner_space = 'LOCAL'
    c.influence = 1

    if foot_toes_bend_axis == '-X':
        min_x = 0
        max_x = radians(180)
        min_z = 0
        max_z = 0

    c = pbone.constraints.new('LIMIT_ROTATION')
    c.name = 'limit rotation'
    c.owner_space = 'LOCAL'
    c.use_transform_limit = True
    c.influence = 1
    c.use_limit_x = True
    c.use_limit_y = True
    c.use_limit_z = True
    c.min_x = min_x
    c.max_x = max_x
    c.min_y = 0
    c.min_y = 0
    c.min_z = min_z
    c.max_z = max_z

    if foot_toes_bend_axis == '-X':
        use_x = True
        use_z = False

    # foot roll back
    pbone = pbones[foot_roll_back]
    c = pbone.constraints.new('COPY_ROTATION')
    c.name = 'copy foot_roll_main'
    c.target = rig
    c.subtarget = foot_roll_main
    c.use_x = use_x
    c.use_y = False
    c.use_z = use_z
    c.invert_x = use_x
    c.invert_y = False
    c.invert_z = use_z
    c.use_offset = False
    c.target_space = 'LOCAL'
    c.owner_space = 'LOCAL'
    c.influence = 1

    if foot_toes_bend_axis == '-X':
        min_x = 0
        max_x = radians(180)
        min_z = 0
        max_z = 0

    c = pbone.constraints.new('LIMIT_ROTATION')
    c.name = 'limit rotation'
    c.owner_space = 'LOCAL'
    c.use_transform_limit = True
    c.influence = 1
    c.use_limit_x = True
    c.use_limit_y = True
    c.use_limit_z = True
    c.min_x = min_x
    c.max_x = max_x
    c.min_y = 0
    c.min_y = 0
    c.min_z = min_z
    c.max_z = max_z

    # foot roll main
    if foot_toes_bend_axis == '-X':
        min_x = radians(-180)
        max_x = radians(180)
        min_z = 0
        max_z = 0

    pbone = pbones[foot_roll_main]
    c = pbone.constraints.new('LIMIT_ROTATION')
    c.name = 'limit rotation'
    c.owner_space = 'LOCAL'
    c.use_transform_limit = True
    c.influence = 1
    c.use_limit_x = True
    c.use_limit_y = True
    c.use_limit_z = True
    c.min_x = min_x
    c.max_x = max_x
    c.min_y = 0
    c.min_y = 0
    c.min_z = min_z
    c.max_z = max_z

    # ik_toes_parent
    if foot_toes_bend_axis == '-X':
        use_x = True
        use_z = False

    pbone = pbones[ik_toes_parent]
    c = pbone.constraints.new('COPY_ROTATION')
    c.name = 'copy foot_roll_front'
    c.target = rig
    c.subtarget = foot_roll_front
    c.use_x = use_x
    c.use_y = False
    c.use_z = use_z
    c.invert_x = True
    c.invert_y = False
    c.invert_z = True
    c.use_offset = True
    c.target_space = 'LOCAL'
    c.owner_space = 'LOCAL'
    c.influence = 1

    bone_visibility(prop_bone_name, module, relevant_bones, ik_ctrl='ik')

    # set module name on relevant bones (used by the 'N-panel' interface)
    set_module_on_relevant_bones(relevant_bone_names, module=module)

    # make the 'Snap&Key' operator recognize this module
    snappable_module(module)
