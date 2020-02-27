#!/usr/bin/env python3.6

import carla
import random
import time

from receive_from_xsens import get_data

SEGMENTS_IDS = {
    1: "Pelvis",
    2: "L5",
    3: "L3",
    4: "T12",
    5: "T8",
    6: "Neck",
    7: "Head",
    8: "Right Shoulder",
    9: "Right Upper Arm",
    10: "Right Forearm",
    11: "Right Hand",
    12: "Left Shoulder",
    13: "Left Upper Arm",
    14: "Left Forearm",
    15: "Left Hand",
    16: "Right Upper Leg",
    17: "Right Lower Leg",
    18: "Right Foot",
    19: "Right Toe",
    20: "Left Upper Leg",
    21: "Left Lower Leg",
    22: "Left Foot",
    23: "Left Toe",
    25: "Prop1",
    26: "Prop2",
    27: "Prop3",
    28: "Prop4",
}

SEG_TO_CARLA = {
    "Left Upper Leg": "crl_thigh__L",
    "Right Upper Leg": "crl_thigh__R",
    "Left Lower Leg": "crl_leg__L",
    "Right Lower Leg": "crl_leg__R",
    "Head": "crl_Head__C",
    "Pelvis": "crl_hips__C",
    "Left Shoulder": "ctrl_shoulder__L",
    "Right Shoulder": "crl_shoulder__R",
    "Left Upper Arm": "crl_arm__L",
    "Right Upper Arm": "crl_arm__R",
    "Left Forearm": "crl_foreArm__L",
    "Right Forearm": "crl_foreArm__R",
    "Left Hand": "crl_hand__L",
    "Right Hand": "crl_hand__R",
    "Neck": "crl_neck__C",
}

START_POINT = dict(x=10, y=20, z=1)
MAIN_POINT = 7


def seg_to_carla(segment_id):
    seg_name = SEGMENTS_IDS[segment_id]
    return SEG_TO_CARLA[seg_name]


def get_location(poseEuler, segment_id, ref_point=None):
    _, *items = poseEuler
    pos, *_ = [poseEuler[1:4] for poseEuler in items if poseEuler[0] == segment_id]

    x, y, z = (n/100 for n in pos)  # Was in cm
    x, y, z = x, -z, y  # Change to right-handed coordinate system

    if ref_point is None:
        return carla.Location(x, y, z)

    x_start, y_start, z_start = START_POINT.values()
    x_ref, y_ref, z_ref = ref_point.values()

    return carla.Location(
        x-x_ref+x_start,
        y-y_ref+y_start,
        z-z_ref+z_start
    )


def get_rotation(poseEuler, segment_id, ref_point=None):
    _, *items = poseEuler
    rotation, *_ = [i[4:7] for i in items if i[0] == segment_id]

    roll, pitch, yaw = rotation
    roll, pitch, yaw = roll, -yaw, pitch  # degrees, right-handed coordinate system

    if ref_point is None:
        return carla.Rotation(pitch, yaw, roll)

    pitch_ref, yaw_ref, roll_ref = ref_point.values()

    return carla.Rotation(
        pitch-pitch_ref,
        yaw-yaw_ref,
        roll-roll_ref
    )


def set_body_transform(poseEuler, walker, ref_point, rotation_ref_point):
    location = get_location(poseEuler, MAIN_POINT, ref_point)
    location = carla.Location(
        x=location.x,
        y=location.y,
        z=walker.get_location().z
    )

    rotation = get_rotation(poseEuler, MAIN_POINT, rotation_ref_point)

    walker.set_transform(carla.Transform(location, rotation))


def main():
    try:
        actor_list = []

        client = carla.Client("localhost", 2000)
        client.set_timeout(5.0)

        world = client.get_world()
        blueprint_library = world.get_blueprint_library()

        location = carla.Location(**START_POINT)

        spectator = world.get_spectator()
        spectator.set_transform(
            carla.Transform(
                location + carla.Location(x=-5, z=1),
                carla.Rotation()
            )
        )

        blueprint = random.choice(blueprint_library.filter('walker.*'))
        walker = world.spawn_actor(blueprint, carla.Transform(location))
        actor_list.append(walker)

        first_data = next(get_data())

        ref_point = get_location(first_data, MAIN_POINT)
        ref_point = dict(x=ref_point.x, y=ref_point.y, z=ref_point.z)

        rotation_ref_point = get_rotation(first_data, MAIN_POINT)
        rotation_ref_point = dict(pitch=rotation_ref_point.pitch, yaw=rotation_ref_point.yaw, roll=rotation_ref_point.roll)

        for poseEuler in get_data():
            _, *items = poseEuler
            seg_ids = [int(i[0]) for i in items]

            for seg_id in seg_ids:
                # set_body_transform(poseEuler, walker, ref_point, rotation_ref_point)

                try:
                    control = carla.WalkerBoneControl()

                    bone = seg_to_carla(seg_id)
                    transform = carla.Transform(
                        get_location(poseEuler, seg_id, ref_point),
                        get_rotation(poseEuler, seg_id, rotation_ref_point)
                    )

                    control.bone_transforms = [(bone, transform)]
                    walker.apply_control(control)
                except KeyError:
                    continue

    finally:
       print('Destroying actors')

       for actor in actor_list:
           actor.destroy()

       print('Done')


if __name__ == "__main__":
    main()
