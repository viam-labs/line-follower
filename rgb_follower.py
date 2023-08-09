"""Module makes a rover follow a line using a webcam for color detection."""

import asyncio

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.base import Base, Vector3
from viam.components.camera import Camera
from viam.services.vision import VisionClient


# Copy and paste the following connect code from the CONNECT tab's Python SDK section
async def connect():
    """
    Connects code to robot.
    """
    creds = Credentials(type="robot-location-secret", payload="<PASTE YOUR SECRET HERE>")
    opts = RobotClient.Options(refresh_interval=0, dial_options=DialOptions(credentials=creds))
    return await RobotClient.at_address("<PASTE YOUR ROBOT'S ADDRESS HERE>", opts)


async def is_color_in_front(camera, detector):
    """
    Returns whether the appropriate path color is detected in front of the center of the robot.
    """
    frame = await camera.get_image(mime_type="image/jpeg")

    x, y = frame.size[0], frame.size[1]

    # Crop the image to get only the middle fifth of the top third of the original image
    cropped_frame = frame.crop((x / 2.5, 0, x / 1.25, y / 3))

    detections = await detector.get_detections(cropped_frame)

    if detections != []:
        return True
    return False


async def is_color_there(camera, detector, location):
    """
    Returns whether the appropriate path color is detected to the left/right of the robot's front.
    """
    frame = await camera.get_image(mime_type="image/jpeg")
    x, y = frame.size[0], frame.size[1]

    if location == "left":
        # Crop image to get only the left two fifths of the original image
        cropped_frame = frame.crop((0, 0, x / 2.5, y))

        detections = await detector.get_detections(cropped_frame)

    elif location == "right":
        # Crop image to get only the right two fifths of the original image
        cropped_frame = frame.crop((x / 1.25, 0, x, y))

        detections = await detector.get_detections(cropped_frame)

    if detections != []:
        return True
    return False


async def stop_robot(robot):
    """
    Stop the robot's motion.
    """
    base = Base.from_robot(robot, "scuttlebase")
    await base.stop()


async def main():
    """
    Main line follower function.
    """
    robot = await connect()
    print("connected")
    camera = Camera.from_robot(robot, "my_camera")
    base = Base.from_robot(robot, "scuttlebase")

    # Put your detector name in place of "green_detector"
    green_detector = VisionClient.from_robot(robot, "green_detector")

    # counter to increase robustness
    counter = 0

    # Speed parameters to experiment with
    linear_power = 0.35
    angular_power = 0.3

    # The main control loop
    while counter <= 3:
        while await is_color_in_front(camera, green_detector):
            print("going straight")
            # Moves the base slowly forward in a straight line
            await base.set_power(Vector3(y=linear_power), Vector3())
            counter == 0
        # If there is green to the left, turns the base left at a continuous, slow speed
        if await is_color_there(camera, green_detector, "left"):
            print("going left")
            await base.set_power(Vector3(), Vector3(z=angular_power))
            counter == 0
        # If there is green to the right, turns the base right at a continuous, slow speed
        elif await is_color_there(camera, green_detector, "right"):
            print("going right")
            await base.set_power(Vector3(), Vector3(z=-angular_power))
            counter == 0
        else:
            counter += 1

    print("The path is behind us and forward is only open wasteland.")

    await stop_robot(robot)
    await robot.close()


if __name__ == "__main__":
    print("Starting up...")
    asyncio.run(main())
    print("Done.")
