from __future__ import annotations

import io
import sys
from pathlib import Path
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
from main import ImageCodec, Header, ThumbnailSize
ProcessImage = ImageCodec.ProcessImage

def MakeImage(P, Mode="RGB", Size=(200, 150), Color=(120, 160, 200)):
    Image.new(Mode, Size, Color).save(P)
    return P

class TestProcess:
    def test_dimensions(self, tmp_path):
        P = MakeImage(tmp_path / "a.png", Size=(800, 600))
        W, H, D = ImageCodec.ProcessImage(P)
        assert (W, H) == (800, 600)
        assert isinstance(D, bytes)
    def test_thumb(self, tmp_path):
        P = MakeImage(tmp_path / "a.png", Size=(1200, 800))
        _, _, D = ImageCodec.ProcessImage(P)
        assert Image.open(io.BytesIO(D)).size == ThumbnailSize
    def test_modes(self, tmp_path):
        for M in ["RGBA", "LA", "P"]:
            P = tmp_path / f"{M}.png"
            Image.new(M, (200, 200)).save(P)
            assert isinstance(ImageCodec.ProcessImage(P)[2], bytes)

class TestEncode:
    def test_header(self, tmp_path):
        P = MakeImage(tmp_path / "a.png")
        Lines = ImageCodec.Encode(str(P))
        assert Lines[0].startswith(Header)
    def test_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ImageCodec.Encode(str(tmp_path / "x.png"))

class TestEdgeCases:
    def test_width(self, tmp_path):
        P = MakeImage(tmp_path / "w.png", Size=(4096, 64))
        O = tmp_path / "out"
        O.mkdir()
        assert Image.open(ImageCodec.Decode(ImageCodec.Encode(str(P)), str(O))).size == (4096, 64)
    def test_height(self, tmp_path):
        P = MakeImage(tmp_path / "t.png", Size=(64, 4096))
        O = tmp_path / "out"
        O.mkdir()
        assert Image.open(ImageCodec.Decode(ImageCodec.Encode(str(P)), str(O))).size == (64, 4096)
    def test_corrupt(self):
        with pytest.raises(Exception):
            ImageCodec.Decode(Header + "!!!bad!!!")
    def test_upper(self, tmp_path):
        P = tmp_path / "A.PNG"
        MakeImage(P)
        Lines = ImageCodec.Encode(str(P))
        assert Lines[0].startswith(Header)
    def test_slots(self):
        C = ImageCodec()
        with pytest.raises(AttributeError):
            C.x = 1