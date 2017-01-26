# UEcron

UEcron is a cron-like that allows you to execute a given program when devices
are added, changed, or removed. This program offers a simpler standalone approach
as opposed to the integrated complex solutions like udev rules. I originally
created this project to monitor virtual devices created in network namespaces
(something that cannot easily be done with udev).

This project directly accesses the kernel's "uevent" system for device
notifications and does not rely on udev in any way.

## Basic usage

```
uecrond --config <path to uetab>
```

Which will start uecron listening for device events. When a device event 
occurs that matches a line in the supplied "uetab" the associated command
will be executed. The "uetab" format follows the standard cron layout:

```
# Device path (everything after /sys)   action          command
/devices/virtual/net/somebr0            add,remove      do_something_great
```

An example uetab is located in the repository

The set of available actions is `add`, `remove` and `change`. Any additional
that was in the event is supplied to the command as environment variables.
The exact set of environment variables changes depending on the event type
and type of device, but the variables will always be prefixed with
`UECRON_`.

### Options

```
usage: uecrond [-h] --config CONFIG [--foreground]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to configuration file
  --foreground, -f      Run in the foreground instead of daemonizing.
```
