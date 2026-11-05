# Robot camera latency: replay image timestamps

A camera on a moving robot observes a fixed landmark. Replay synthetic poses and compare the landmark positions obtained by using the camera pose at capture and at arrival.

## Run it

Install [Python 3.10 or newer](https://www.python.org/downloads/). Download the GitHub ZIP and extract it, then open a terminal in the folder containing `align.py`. The analyzer and tests use only the standard library. On Windows use `py -3` in place of `python3`.

```text
python3 --version
python3 align.py examples/moving.json
python3 align.py examples/stationary.json
python3 align.py examples/rejected.json
python3 -m unittest discover -s tests -v
```

The moving example reconstructs 100 mm for both frames. Using the arrival pose instead gives 112 mm and 104 mm. The stationary camera produces no arrival bias. The last example shows an old frame, a gap in pose history, a capture outside the recorded interval, and a valid frame with no available arrival pose.

## Change the inputs

Copy an example. Use integer milliseconds from one time base. Keep camera samples strictly increasing. Distances use millimetres along one shared positive X direction. Try `--max-age-ms 50` with the moving example to discard its first frame. Leave the pose gap threshold at 50 ms for that experiment.

An arrival before capture usually means the clocks or the units need checking. Do not sort the frames to hide that error. A pose gap can be caused by missing telemetry; the analyzer will not extrapolate. If Python cannot find the script, change to the extracted folder.

## Scope

Synthetic 1D positions only. This example neither reads real images nor sends robot commands. It assumes a fixed camera orientation and synchronized timestamps and does not validate a driver, calibration, rolling shutter, or hardware timing. The WebP diagrams are generated from the included examples. To regenerate them, use Pillow and the DejaVu Sans font path shown in `diagrams/render.py`; these are optional and are not needed for the lab.

Full lesson: https://wifarobotics.com/learn/robot-camera-latency/
