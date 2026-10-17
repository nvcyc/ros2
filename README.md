# About
The Robot Operating System (ROS) is a set of software libraries and tools that help you build robot applications.
From drivers to state-of-the-art algorithms, and with powerful developer tools, ROS has what you need for your next robotics project.
And it's all open source.
Full project details on [ROS.org](https://ros.org/)

# Building

This development workspace follows ROS 2 rolling and includes
[`rosidl_buffer_dev`](https://github.com/nvcyc/rosidl_buffer_dev),
[`rosidl_buffer_backends`](https://github.com/ros2/rosidl_buffer_backends), and
[`rosidl_buffer_backends_tutorials`](https://github.com/ros2/rosidl_buffer_backends_tutorials).

Install Git and [Pixi](https://pixi.sh) (version 0.78 or newer), then clone this branch:

```bash
git clone --branch rolling-dev https://github.com/nvcyc/ros2.git
cd ros2
```

`rosidl_buffer_dev` is private. Configure Git HTTPS authentication for your GitHub
account with access to that repository before importing sources.

Build one or more packages and their dependencies:

```bash
pixi run build cuda_buffer cuda_buffer_backend
```

The first build installs the Pixi environment and imports the source repositories.
On Linux, the environment includes CUDA Toolkit >=13.1,<14 and the rolling GCC
toolchain; the lockfile records exact versions. Running GPU examples and tests
also requires a compatible NVIDIA driver and GPU on the host. CUDA tooling is
currently provided by this manifest only on Linux x86-64.

To import sources explicitly, use `pixi run clone`. After changing `ros2.repos`,
import directly to bypass the clone task’s existing-file cache:

```bash
pixi run vcs import --input ros2.repos src
```

Build dependencies and test only the named packages, or include dependency tests:

```bash
pixi run test cuda_buffer cuda_buffer_backend
pixi run test-up-to cuda_buffer_backend
```

To test without rebuilding, use `pixi run test-only`. Test failures produce a
nonzero exit status, followed by a workspace-wide `colcon test-result --verbose`
summary. That summary may include older results from packages outside this run.

Select CTest tests with a quoted regular expression:

```bash
pixi run test cuda_buffer cuda_buffer_backend --tests-to-run 'allocation|ipc'
```

This filter applies to CTest tests; it does not filter standalone pytest packages.
Omitting package names builds or tests the whole workspace.

For local build concurrency settings, copy `.env.example` to `.env` and adjust
`PIXI_PARALLEL_WORKERS`. `.env` is ignored by Git.

The compilation database workflow continues to use compdb:

```bash
pixi run compile-commands cuda_buffer cuda_buffer_backend
```

Use `pixi task list` to see all commands. When changing dependencies, regenerate
`pixi.lock` with Pixi 0.78.0, matching the version used by the lockfile CI check.

# Getting Started
Looking to get started with ROS?
Our [installation guide is here](https://www.ros.org/blog/getting-started/).
Once you've installed ROS start by learning some [basic concepts](https://docs.ros.org/en/rolling/Concepts/Basic.html) and take a look at our [beginner tutorials](https://docs.ros.org/en/rolling/Tutorials/Beginner-CLI-Tools.html).

# Join the ROS Community

## Community Resources

* [ROS Discussion Forum](https://discourse.ros.org/)
* [ROS Zulip Server](https://openrobotics.zulipchat.com/)
* [Robotics Stack Exchange](https://robotics.stackexchange.com/) (preferred ROS support forum).
* [Official ROS Videos](https://vimeo.com/osrfoundation)
* [ROSCon](https://roscon.ros.org), our yearly developer conference.
* Cite ROS 2 in academic work using [DOI: 10.1126/scirobotics.abm6074](https://www.science.org/doi/10.1126/scirobotics.abm6074)

## Developer Resources
* [ROS 2 Documentation](https://docs.ros.org/)
* [ROS 2 API docs (rclcpp, rclpy, packages)](https://docs.ros.org/en/rolling/p/)
* [ROS Package Index](https://index.ros.org/)
* [ROS on Docker Hub](https://hub.docker.com/_/ros/)
* [ROS Resource Status Page](https://status.openrobotics.org/)
* [REP-2000](https://ros.org/reps/rep-2000.html): ROS 2 Releases and Target Platforms

## Project Resources
* [Purchase ROS Swag](https://spring.ros.org/)
* [Information about the ROS Trademark](https://www.ros.org/blog/media/)
* On Social Media
  * [Open Robotics on LinkedIn](https://www.linkedin.com/company/open-source-robotics-foundation)
  * [Open Robotics on Twitter](https://twitter.com/OpenRoboticsOrg)
  * [ROS.org on Twitter](https://twitter.com/ROSOrg)

ROS is made possible through the generous support of open source contributors and the non-profit [Open Source Robotics Foundation (OSRF)](https://www.openrobotics.org/).
Tax deductible donations to the OSRF can be [made here.](https://donorbox.org/support-open-robotics?utm_medium=qrcode&utm_source=qrcode)
