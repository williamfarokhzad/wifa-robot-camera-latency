"""Compare capture-time and arrival-time position estimates in a 1D replay."""
import argparse
from bisect import bisect_left
import json
from pathlib import Path


def milliseconds(value, label):
    if type(value) is not int or not 0 <= value <= 10**12:
        raise ValueError(f"{label} must be a nonnegative integer in ms (at most 10^12)")
    return value


def position(value, label):
    if type(value) not in (int, float) or not -1e9 <= value <= 1e9:
        raise ValueError(f"{label} must be a finite number between ±10^9 mm")
    return float(value)


def sample_pose(times, positions, time_ms, max_gap_ms):
    i = bisect_left(times, time_ms)
    if i < len(times) and times[i] == time_ms:
        return positions[i], None
    if i == 0 or i == len(times):
        return None, "outside_pose_history"
    gap = times[i] - times[i - 1]
    if gap > max_gap_ms:
        return None, "pose_gap_too_large"
    fraction = (time_ms - times[i - 1]) / gap
    return positions[i - 1] + fraction * (positions[i] - positions[i - 1]), None


def replay(record, max_age_ms, max_gap_ms):
    milliseconds(max_age_ms, "max_age_ms")
    milliseconds(max_gap_ms, "max_gap_ms")
    if not max_gap_ms:
        raise ValueError("max_gap_ms must be positive")
    if not isinstance(record, dict) or not all(isinstance(record.get(k), list) and record[k]
                                                for k in ("poses", "frames")):
        raise ValueError("provide a JSON object with nonempty poses and frames lists")
    times, positions = [], []
    for p in record["poses"]:
        t = milliseconds(p["time_ms"], "pose time_ms")
        if times and t <= times[-1]:
            raise ValueError("pose timestamps must be strictly increasing")
        times.append(t)
        positions.append(position(p["camera_x_mm"], "camera_x_mm"))
    rows = []
    for frame in record["frames"]:
        captured = milliseconds(frame["capture_ms"], "capture_ms")
        received = milliseconds(frame["arrival_ms"], "arrival_ms")
        relative = position(frame["target_from_camera_mm"], "target_from_camera_mm")
        if received < captured:
            raise ValueError("arrival precedes capture; verify clock alignment")
        age = received - captured
        row = dict(capture_ms=captured, arrival_ms=received, age_ms=age)
        if age > max_age_ms:
            rows.append(dict(row, status="stale"))
            continue
        capture_pose, error = sample_pose(times, positions, captured, max_gap_ms)
        if error:
            rows.append(dict(row, status=error))
            continue
        arrival_pose, _ = sample_pose(times, positions, received, max_gap_ms)
        by_arrival = None if arrival_pose is None else arrival_pose + relative
        by_capture = capture_pose + relative
        rows.append(dict(row, status="ok", target_at_capture_mm=by_capture,
                         target_using_arrival_mm=by_arrival,
                         arrival_bias_mm=None if by_arrival is None else arrival_pose - capture_pose))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--max-age-ms", type=int, default=80)
    parser.add_argument("--max-gap-ms", type=int, default=50)
    args = parser.parse_args()
    try:
        rows = replay(json.loads(args.record.read_text(encoding="utf-8")),
                      args.max_age_ms, args.max_gap_ms)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(rows, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
