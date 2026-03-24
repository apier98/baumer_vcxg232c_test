from __future__ import annotations

import unittest

from src.camera_test import _lookup_feature, _write_feature_value


class FakeFloatFeature:
    def __init__(self, name: str, value: float = 4000.0) -> None:
        self._name = name
        self.value = value

    def GetName(self) -> str:
        return self._name

    def IsReadable(self) -> bool:
        return True

    def IsWritable(self) -> bool:
        return True

    def GetInterface(self) -> str:
        return "IFloat"

    def GetValue(self) -> float:
        return self.value

    def SetValue(self, value: float) -> None:
        self.value = float(value)


class FakeFeatureCollection:
    def __init__(self, *features: object) -> None:
        for feature in features:
            setattr(self, feature.GetName(), feature)


class FakeCamera:
    def __init__(self, *features: object) -> None:
        self._features = list(features)
        self.f = FakeFeatureCollection(*features)

    def GetFeature(self, name: str) -> object:
        for feature in self._features:
            if feature.GetName() == name:
                return feature
        raise KeyError(name)

    def GetFeatureList(self) -> list[object]:
        return list(self._features)


class CameraFeatureHelpersTests(unittest.TestCase):
    def test_write_feature_value_uses_numeric_setter_for_float_features(self) -> None:
        feature = FakeFloatFeature("ExposureTime", value=4000.0)

        _write_feature_value(feature, "10000")

        self.assertEqual(feature.value, 10000.0)

    def test_lookup_feature_allows_unique_prefix_match(self) -> None:
        exposure_time = FakeFloatFeature("ExposureTime")
        camera = FakeCamera(exposure_time)

        resolved = _lookup_feature(camera, "Exposure")

        self.assertIs(resolved, exposure_time)

    def test_lookup_feature_allows_case_insensitive_exact_match(self) -> None:
        exposure_time = FakeFloatFeature("ExposureTime")
        camera = FakeCamera(exposure_time)

        resolved = _lookup_feature(camera, "exposuretime")

        self.assertIs(resolved, exposure_time)


if __name__ == "__main__":
    unittest.main()
