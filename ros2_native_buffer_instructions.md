Install some Rolling specific packages that are missing from the dev container.
`sudo apt update && sudo apt install ros-rolling-ros2cli ros-rolling-ros2run ros-rolling-launch-ros ros-rolling-launch-testing ros-rolling-launch-testing-ament-cmake ros-rolling-rclcpp-components`

Set up custom repositories:
`vcs import src < ros2_native_buffer.repos`

Install dependencies needed from the packages being imported:
`rosdep install --from-paths src --ignore-src -y`

When running `colcon build` remember to always add override flag to use the packages built from source under this repo:
`--allow-overriding $(colcon list --names-only --base-paths /workspaces/ros2/src | tr '\n' ' ')`

If building the first time, first build `rmw_zenoh_cpp` so at least there is one RMW implementation that can be installed in the environment.
`colcon build --symlink-install --packages-up-to rmw_zenoh_cpp --allow-overriding $(colcon list --names-only --base-paths /workspaces/ros2/src | tr '\n' ' ')`

Then install:
`source install/setup.bash`

Then build with the packaegs you desired with colcon build again:
`colcon build --symlink-install --allow-overriding $(colcon list --names-only --base-paths /workspaces/ros2/src | tr '\n' ' ')`

Run Zenoh server in a separate terminal:
`ros2 run rmw_zenoh_cpp rmw_zenohd`

Run tests:
- `export RCL_LOGGING_IMPLEMENTATION=rcl_logging_noop && source install/setup.bash && timeout 30 ./install/test_buffer_compatibility/lib/test_buffer_compatibility/test_image_pubsub`
- `launch_test src/ros2/rcl_buffer/test_rcl_buffer/test/test_test_backend_image_pubsub_launch.py`