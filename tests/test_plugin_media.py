import queue
import types
import unittest

try:
    from piweatherrock.plugin_media import PluginMedia
except ModuleNotFoundError as exc:
    if exc.name != "pygame":
        raise
    PluginMedia = None


class DummyProcess:
    def __init__(self, returncode=None):
        self.returncode = returncode

    def poll(self):
        return self.returncode


@unittest.skipIf(PluginMedia is None, "pygame is not installed")
class PluginMediaVideoReadTest(unittest.TestCase):
    def setUp(self):
        weather_rock = types.SimpleNamespace(
            config={
                "plugins": {
                    "media": {
                        "path": "",
                        "shuffle": False,
                        "fit": "contain",
                        "extensions": "",
                    }
                }
            },
            screen=None,
            log=types.SimpleNamespace(
                warning=lambda *args, **kwargs: None,
                exception=lambda *args, **kwargs: None,
                info=lambda *args, **kwargs: None,
            ),
            xmax=2,
            ymax=2,
        )
        self.plugin = PluginMedia(weather_rock)

    def test_read_video_frame_uses_queued_reader_frame(self):
        self.plugin.video_process = DummyProcess()
        self.plugin.video_frames.put(b"frame")

        self.assertEqual(self.plugin._read_video_frame("clip.mp4"), b"frame")

    def test_read_video_frame_reports_eof_after_process_exits(self):
        self.plugin.video_process = DummyProcess(returncode=0)
        self.plugin.video_frames = queue.Queue()
        self.plugin.VIDEO_READ_TIMEOUT = 0.01

        self.assertEqual(self.plugin._read_video_frame("clip.mp4"), b"")


if __name__ == "__main__":
    unittest.main()
