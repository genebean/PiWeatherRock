# -*- coding: utf-8 -*-
"""Local media screen for images and short videos."""

import math
import os
import queue
import random
import subprocess
import threading
import time

import pygame

from piweatherrock.config_manager import (
    MEDIA_IMAGE_EXTENSIONS,
    MEDIA_VIDEO_EXTENSIONS,
    expand_config_path,
)


class PluginMedia:
    """Displays images and short videos from a configured local folder."""

    SCAN_INTERVAL = 30
    FONT_SIZE_RATIO = 0.06
    VIDEO_READ_TIMEOUT = 0.2

    def __init__(self, weather_rock):
        self.config = None
        self.screen = None
        self.log = None
        self.xmax = None
        self.ymax = None
        self.media_config = None
        self.items = []
        self.current_index = -1
        self.current_item = None
        self.current_surface = None
        self.video_process = None
        self.video_reader = None
        self.video_frames = queue.Queue(maxsize=2)
        self.video_failed_path = None
        self.last_scan = 0
        self.signature = None
        self.get_rock_values(weather_rock)

    def get_rock_values(self, weather_rock):
        self.config = weather_rock.config
        self.screen = weather_rock.screen
        self.log = weather_rock.log
        self.xmax = int(weather_rock.xmax)
        self.ymax = int(weather_rock.ymax)
        self.media_config = self.config["plugins"]["media"]

    def on_enter(self, weather_rock):
        self.get_rock_values(weather_rock)
        self._scan_if_needed(force=True)
        self._next_item()

    def on_exit(self):
        self._stop_video()

    def disp_media(self, weather_rock):
        self.get_rock_values(weather_rock)
        self._scan_if_needed()
        if not self.current_item:
            self._next_item()

        if not self.current_item:
            self._render_message("No local media files found")
            return

        path, kind = self.current_item
        if kind == "image":
            if self.current_surface is None:
                self.current_surface = self._load_image(path)
            if self.current_surface is None:
                self._next_item()
                return
            self.screen.blit(self.current_surface, (0, 0))
            pygame.display.update()
        else:
            if self.video_failed_path == path:
                self._render_message("Video playback requires ffmpeg")
                return
            if self.video_process is None:
                self.video_process = self._start_video(path)
            if self.video_process is None:
                self.video_failed_path = path
                self._render_message("Video playback requires ffmpeg")
                return
            frame = self._read_video_frame(path)
            if frame is None:
                return
            if not frame:
                self.log.info("Finished media video %s", path)
                self._next_item()
                return
            surface = pygame.image.frombuffer(frame, (self.xmax, self.ymax), "RGB")
            self.screen.blit(surface, (0, 0))
            pygame.display.update()

    def _scan_if_needed(self, force=False):
        signature = self._config_signature()
        now = time.time()
        if (not force and signature == self.signature
                and now - self.last_scan < self.SCAN_INTERVAL):
            return

        self.signature = signature
        self.last_scan = now
        media_path = expand_config_path(self.media_config.get("path", ""))
        if not os.path.isdir(media_path):
            self.items = []
            return

        image_ext = set(MEDIA_IMAGE_EXTENSIONS)
        video_ext = set(MEDIA_VIDEO_EXTENSIONS)
        configured_ext = self._configured_extensions()
        items = []
        try:
            names = sorted(os.listdir(media_path))
        except OSError:
            self.log.exception("Could not scan media directory %s", media_path)
            self.items = []
            return

        for name in names:
            full_path = os.path.join(media_path, name)
            if not os.path.isfile(full_path):
                continue
            extension = os.path.splitext(name)[1].lower().lstrip(".")
            if extension not in configured_ext:
                continue
            if extension in image_ext:
                items.append((full_path, "image"))
            elif extension in video_ext:
                items.append((full_path, "video"))

        if self.media_config.get("shuffle"):
            random.shuffle(items)
        self.items = items
        if self.current_item not in self.items:
            self.current_index = -1
            self.current_item = None
            self.current_surface = None
            self._stop_video()

    def _configured_extensions(self):
        return set(
            part.strip().lower().lstrip(".")
            for part in self.media_config.get("extensions", "").split(",")
            if part.strip()
        )

    def _config_signature(self):
        return (
            self.media_config.get("path"),
            self.media_config.get("shuffle"),
            self.media_config.get("fit"),
            self.media_config.get("extensions"),
            self.xmax,
            self.ymax,
        )

    def _next_item(self):
        self._stop_video()
        self.current_surface = None
        self.video_failed_path = None
        if not self.items:
            self.current_index = -1
            self.current_item = None
            return
        self.current_index = (self.current_index + 1) % len(self.items)
        self.current_item = self.items[self.current_index]

    def _load_image(self, path):
        try:
            image = pygame.image.load(path).convert()
            return self._fit_surface(image)
        except Exception:
            self.log.exception("Could not load media image %s", path)
            return None

    def _fit_surface(self, surface):
        fit = self.media_config.get("fit", "contain")
        if fit not in ("contain", "cover", "stretch"):
            self.log.warning("Unsupported media fit mode %s; using contain", fit)
            fit = "contain"
        width, height = surface.get_size()
        if fit == "stretch":
            return pygame.transform.smoothscale(surface, (self.xmax, self.ymax))

        if fit == "contain":
            scale = min(self.xmax / width, self.ymax / height)
        else:
            scale = max(self.xmax / width, self.ymax / height)
        if fit == "cover":
            new_size = (
                max(self.xmax, int(math.ceil(width * scale))),
                max(self.ymax, int(math.ceil(height * scale))),
            )
        else:
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        scaled = pygame.transform.smoothscale(surface, new_size)

        if fit == "cover":
            left = max(0, int((new_size[0] - self.xmax) / 2))
            top = max(0, int((new_size[1] - self.ymax) / 2))
            return scaled.subsurface((left, top, self.xmax, self.ymax)).copy()

        canvas = pygame.Surface((self.xmax, self.ymax))
        canvas.fill((0, 0, 0))
        left = int((self.xmax - new_size[0]) / 2)
        top = int((self.ymax - new_size[1]) / 2)
        canvas.blit(scaled, (left, top))
        return canvas

    def _start_video(self, path):
        fit = self.media_config.get("fit", "contain")
        if fit not in ("contain", "cover", "stretch"):
            self.log.warning("Unsupported media fit mode %s; using contain", fit)
            fit = "contain"
        if fit == "cover":
            video_filter = (
                "scale={0}:{1}:force_original_aspect_ratio=increase,"
                "crop={0}:{1}"
            ).format(self.xmax, self.ymax)
        elif fit == "stretch":
            video_filter = "scale={}:{}".format(self.xmax, self.ymax)
        else:
            video_filter = (
                "scale={0}:{1}:force_original_aspect_ratio=decrease,"
                "pad={0}:{1}:(ow-iw)/2:(oh-ih)/2:black"
            ).format(self.xmax, self.ymax)

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-re",
            "-i",
            path,
            "-vf",
            video_filter,
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ]
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL)
        except OSError:
            self.log.warning("ffmpeg is not available for video playback")
            return None

        frame_size = self.xmax * self.ymax * 3
        frames = queue.Queue(maxsize=2)
        self.video_frames = frames
        self.video_reader = threading.Thread(
            target=self._read_video_frames,
            args=(process, path, frame_size, frames))
        self.video_reader.daemon = True
        self.video_reader.start()
        return process

    def _stop_video(self):
        process = self.video_process
        if process is None:
            return

        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if self.video_reader is not None:
            self.video_reader.join(timeout=1)
        if process.stdout is not None:
            process.stdout.close()
        self.video_process = None
        self.video_reader = None
        self.video_frames = queue.Queue(maxsize=2)

    def _is_video_playing(self):
        return self.video_process is not None

    def _read_video_frames(self, process, path, frame_size, frames):
        try:
            while True:
                frame = self._read_exact_frame(process.stdout, frame_size)
                if len(frame) < frame_size:
                    break
                self._queue_video_frame(frames, frame)
        except OSError:
            self.log.exception("Could not read media video %s", path)
        finally:
            self._queue_video_frame(frames, b"")

    def _read_exact_frame(self, stream, frame_size):
        if stream is None:
            return b""
        frame = b""
        while len(frame) < frame_size:
            chunk = stream.read(frame_size - len(frame))
            if not chunk:
                break
            frame += chunk
        return frame

    def _queue_video_frame(self, frames, frame):
        try:
            frames.put_nowait(frame)
            return
        except queue.Full:
            pass

        try:
            frames.get_nowait()
        except queue.Empty:
            pass
        try:
            frames.put_nowait(frame)
        except queue.Full:
            pass

    def _read_video_frame(self, path):
        process = self.video_process
        try:
            return self.video_frames.get(timeout=self.VIDEO_READ_TIMEOUT)
        except queue.Empty:
            if process.poll() is not None:
                return b""
            return None

    def _render_message(self, message):
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(
            "freesans", max(18, int(self.ymax * self.FONT_SIZE_RATIO)))
        rendered = font.render(message, True, (255, 255, 255))
        width, height = rendered.get_size()
        self.screen.blit(
            rendered,
            ((self.xmax - width) / 2, (self.ymax - height) / 2))
        pygame.display.update()
