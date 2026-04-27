from __future__ import annotations

__all__ = [
    "ImageCodec",
    "Header",
    "ThumbnailSize",
    "ThumbnailColors",
    "FileTypes",
    "HeaderSize",
    "Structure",
]

import base64
import io
import struct
import sys
import zlib
import json
from pathlib import Path
from typing import Final
from PIL import Image

def _load_version() -> str:
    version_path = Path(__file__).resolve().parent / "version"
    return json.loads(version_path.read_text(encoding="utf-8"))["version"]
Version = _load_version()

ThumbnailSize: Final[tuple[int, int]] = (256, 144)
ThumbnailColors: Final[int] = 64
Header: Final[str] = "IMEXT"

FileTypes: Final[dict[str, str]] = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".gif": "GIF",
    ".bmp": "BMP",
    ".webp": "WEBP",
}

Structure: Final[str] = ">II"
HeaderSize: Final[int] = struct.calcsize(Structure)


class ImageCodec:
    __slots__ = ()
    ChunkSize = 1800
    
    @staticmethod
    def ProcessImage(Source: Path) -> tuple[int, int, bytes]:
        with Image.open(Source) as Photo:
            Photo = Photo.convert("RGBA") if Photo.mode in ("RGBA", "LA", "P") else Photo.convert("RGB")
            OriginalWidth, OriginalHeight = Photo.size
            Thumbnail = Photo.resize(ThumbnailSize, Image.LANCZOS)
            Thumbnail = Thumbnail.quantize(colors=ThumbnailColors).convert("RGB")
        Buffer = io.BytesIO()
        Thumbnail.save(Buffer, format="PNG", optimize=True)
        return OriginalWidth, OriginalHeight, Buffer.getvalue()
    
    @staticmethod
    def Encode(ImagePath: str) -> list[str]:
        Source = Path(ImagePath)
        if not Source.is_file():
            raise FileNotFoundError(ImagePath)
        Width, Height, ImageBytes = ImageCodec.ProcessImage(Source)
        Extension = Source.suffix.lower().encode("ascii")
        Payload = (
            struct.pack(">B", len(Extension)) +
            Extension +
            struct.pack(Structure, Width, Height) +
            ImageBytes
        )
        OriginalSize = Source.stat().st_size
        Compressed = zlib.compress(Payload, 9)
        UseCompression = len(Compressed) < len(Payload)
        EncodedPayload = Compressed if UseCompression else Payload
        Encoded = base64.urlsafe_b64encode(EncodedPayload).decode("ascii").rstrip("=")
        FinalSize = len(Encoded)
        CompressionRate = round((1 - FinalSize / OriginalSize) * 100, 2)
        Chunks = [
            Encoded[i:i + ImageCodec.ChunkSize]
            for i in range(0, len(Encoded), ImageCodec.ChunkSize)
        ]
        Total = len(Chunks)
        Lines = [f"{Header}|v{Version}|meta|{int(UseCompression)}|{Total}|{CompressionRate}"]
        for Index, Chunk in enumerate(Chunks):
            Lines.append(f"{Header}|v{Version}|chunk|{Index}|{Total}|:{Chunk}:")
        ImageCodec._LastCompressionRate = CompressionRate
        return Lines
    
    @staticmethod
    def Decode(Lines: list[str], OutputDir: str | None = None) -> Path:
        if not Lines:
            raise ValueError("Empty input")
        Meta = Lines[0].split("|")
        if len(Meta) < 6 or Meta[0] != Header or Meta[1] != f"v{Version}":
            raise ValueError("Invalid header")
        UseCompression = int(Meta[3])
        Total = int(Meta[4])
        CompressionRate = float(Meta[5])
        Parts: list[str | None] = [None] * Total
        for Line in Lines[1:]:
            _, _, _, Index, _, Data = Line.split("|", 5)
            Parts[int(Index)] = Data[1:-1]
        if any(Part is None for Part in Parts):
            raise ValueError("Missing chunks")
        Combined = "".join(Parts)
        Padding = "=" * (-len(Combined) % 4)
        Raw = base64.urlsafe_b64decode(Combined + Padding)
        if UseCompression:
            Raw = zlib.decompress(Raw)
        ExtensionLength = Raw[0]
        Extension = Raw[1:1 + ExtensionLength].decode("ascii")
        Rest = Raw[1 + ExtensionLength:]
        Width, Height = struct.unpack(Structure, Rest[:HeaderSize])
        ImageData = Rest[HeaderSize:]
        ImageObject = Image.open(io.BytesIO(ImageData))
        ImageObject = ImageObject.resize((Width, Height), Image.LANCZOS)
        Base = Path(OutputDir) if OutputDir else Path.cwd()
        Output = Base / f"decoded{Extension}"
        Buffer = io.BytesIO()
        ImageObject.save(Buffer, format=FileTypes.get(Extension, "PNG"), optimize=True)
        Output.write_bytes(Buffer.getvalue())
        return Output

def Main() -> None:
    if len(sys.argv) < 2:
        print("Usage: encode <file> ; decode <file> [dir]")
        sys.exit(1)
    match sys.argv[1].lower():
        case "encode":
            Lines = ImageCodec.Encode(sys.argv[2])
            Source = Path(sys.argv[2])
            Output = Source.parent / f"{Source.stem}_imext.txt"
            Output.write_text("\n".join(Lines), encoding="ascii")
            CompressionRate = float(Lines[0].split("|")[5])
            print(
                f"{Output} ({len(Lines)} lines) ; "
                f"(Compression Rate: {CompressionRate}%)"
            )
        case "decode":
            Lines = Path(sys.argv[2]).read_text(encoding="ascii").splitlines()
            Output = ImageCodec.Decode(
                Lines,
                sys.argv[3] if len(sys.argv) == 4 else None
            )
            CompressionRate = float(Lines[0].split("|")[5])
            print(f"{Output} (Compression Rate: {CompressionRate}%)")
        case _:
            print("Usage: encode <file> ; decode <file> [dir]")
            sys.exit(1)

if __name__ == "__main__":
    Main()