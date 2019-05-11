import bpy
from mathutils.bvhtree import BVHTree


class Globals():
        
    auto_bone_shape_scale_offset = 0.05
    auto_bone_shape_scale_offset_limb = 0.02
    target_shape_size = 0.05
    general_bone_size = 0.05
    pole_target_distance = 0.5
    finger_shape_size = 0.01
    face_shape_size = 0.005
    look_target_size = face_shape_size * 5
    look_target_offset = 0.5
    chest_target_distance = 1
    chest_target_size = 0.25

    source_path = os.path.dirname(__file__) + "/source_shapes.blend"

    # BIPED:
    # root
    root_size = 0.25
    root_extract_size = 0.15

    # TWIST BONES:
    neck_twist_rotate_back = 0.5
    neck_twist_min_y = -20
    neck_twist_track_to_head = 1

    twist_target_distance = -0.4

    # upperarm
    upperarm_twists = [
        [0.75],
        [0.75, 0.5],
        [0.75, 0.5, 0.25]
    ]

    # forearm
    forearm_twists = [
        [1],
        [1, 0.5],
        [1, 0.5, 0.25]
    ]

    # thigh
    thigh_twists = [
        [0.75],
        [0.75, 0.5],
        [0.75, 0.5, 0.25]
    ]

    # shin
    shin_twists = [
        [0.75],
        [1, 0.5],
        [1, 0.5, 0.25]
    ]

    # SPRING BONES (left):
    spring_bottom__thigh_bend_fwd_to_scale__thigh_rot = 45
    spring_bottom__thigh_bend_fwd_to_scale__scale = 1.4
    spring_bottom__thigh_bend_fwd_to_rot__thigh_rot = 90
    spring_bottom__thigh_bend_fwd_to_rot__rot = 60

    spring_bottom__thigh_bend_bwd_to_scale__thigh_rot = -30
    spring_bottom__thigh_bend_bwd_to_scale__scale = 1.4
    spring_bottom__thigh_bend_bwd_to_rot__thigh_rot = -30
    spring_bottom__thigh_bend_bwd_to_rot__rot = -10

    spring_belly__waist_lower_rot_to_scale__waist_lower_rot = 30
    spring_belly__waist_lower_rot_to_scale__scale = 2

    spring_chest__shoulder_up__shoulder_rot = 60
    spring_chest__shoulder_up__rot = 30
    spring_chest__shoulder_down__shoulder_rot = -20
    spring_chest__shoulder_down__rot = -5

    # FACIAL BONES
    teeth_lower_copy_jaw_rot = 0.7
    lowerlip_copy_jaw_rot = 0.5
    upperlid_copy_eye_rot = 0.25
    lowerlid_copy_eye_rot = 0.1

    # CTRL FINGERS (left):
    ctrl_finger_scale__to_finger_2_3_bend_fwd__scale = 0.5
    ctrl_finger_scale__to_finger_2_3_bend_fwd__rot = -90
    ctrl_finger_scale__to_finger_2_3_bend_bwd__scale = 1.25
    ctrl_finger_scale__to_finger_2_3_bend_bwd__rot = 10

    ctrl_finger_scale__to_thumb_2_bend_fwd__rot = -75
    ctrl_finger_scale__to_thumb_2_bend_bwd__rot = 30

    # CTRL SPINE
    ctrl_waist__copy__ctrl_chest = 1.0
    ctrl_waist__copy__ctrl_hips = 0.6

    ik_spine_2__copy__ctrl_waist = 0.6
    ik_spine_2__copy__ctrl_waist = 0.5

    fixate_ctrl_neck = 0.3
    fixate_ctrl_head = 0.5

    # MISC
    sides = ['_l', '_r']
    fk_prefix = 'fk_'
    ik_prefix = 'ik_'

    # LAYERS
    # game bones
    base_layer = 0
    twist_layer = 1
    spring_layer = 2
    fix_layer = 3
    face_layer = 4
    face_extra_layer = 5
    ik_prop_layer = 6

    root_layer = 16

    misc_layer = 24
    twist_target_layer = 25
    fk_extra_layer = 26
    ctrl_ik_extra_layer = 27
    module_prop_layer = 28

    fk_layer = 8
    ctrl_ik_layer = 9
    touch_layer = 10

    target_layer = 11

    # GROUPS
    base_group = 'base'
    fk_group = 'fk'
    central_ik_group = 'ik_c'
    left_ik_group = 'ik_l'
    right_ik_group = 'ik_r'
    twist_group = 'twist'
    spring_group = 'spring'
    ik_prop_group = 'ik_prop'
    face_group = 'face'
    target_group = 'target'
