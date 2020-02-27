#!/usr/bin/env python3.6

import carla
import random
import time

from receive_from_xsens import get_data


# Based on observations
REF_POINT = dict(x=0.04352539, y=-0.35641365, z=0.06725183)
START_POINT = dict(x=10, y=20, z=1)


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

        location.x += 2
        blueprint = random.choice(blueprint_library.filter('walker.*'))
        walker = world.spawn_actor(blueprint, carla.Transform(location))

        actor_list.append(walker)

        for d in get_data():
            _, *items = d

            pos, *_ = [i[1:4] for i in items if i[0] == 1]
            x, y, z = (n/100 for n in pos) 

            x, y, z = x, -z, y  # Change to right-handed coordinate system

            x_ref, y_ref, z_ref = REF_POINT.values()
            x_start, y_start, z_start = START_POINT.values()

            location = carla.Location(
                x-x_ref+x_start,
                y-y_ref+y_start,
                z-z_ref+z_start
            )
            walker.set_location(location)

            print(location)

    finally:
       print('destroying actors')
       for actor in actor_list:
           actor.destroy()
       print('done.')


if __name__ == "__main__":
	main()
