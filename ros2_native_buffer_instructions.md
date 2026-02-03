Install some Rolling specific packages that are missing from the dev container.
`sudo apt update && sudo apt install ros-rolling-ros2cli ros-rolling-ros2run`

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

Run Zenoh server:
`ros2 run rmw_zenoh_cpp rmw_zenohd`
