# About
The Robot Operating System (ROS) is a set of software libraries and tools that help you build robot applications.
From drivers to state-of-the-art algorithms, and with powerful developer tools, ROS has what you need for your next robotics project.
And it's all open source.
Full project details on [ROS.org](https://ros.org/)

# Building
First, install git if not installed already:
```
sudo apt install -y git
```

Then, install pixi:

```
curl -fsSL https://pixi.sh/install.sh | sh
```

Now, clone this repository:

```
git clone https://github.com/karsten-nvidia/ros2.git && cd ros2
```

Now `pixi` can be used to perform the most important steps. To build a package like rclcpp, use

```
pixi run build rclcpp
```

Note that the above command will automatically install the environment and clone all required source code, so it will take a while.

To run tests, use

```
pixi run test rclcpp
```

To see all available commands, use

```
pixi task list
```

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
