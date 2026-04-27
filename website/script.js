let pyodide;

async function init() {
    pyodide = await loadPyodide();
    await pyodide.loadPackage(["pillow"]);

    await pyodide.runPythonAsync(`
    import base64, io, struct, zlib, json
    from pathlib import Path
    from PIL import Image
    import os

    Header = "IMEXT"
    ThumbnailSize = (256, 144)
    ThumbnailColors = 64
    Structure = ">II"
    HeaderSize = struct.calcsize(Structure)
    ChunkSize = 1800

    def ProcessImage(data):
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGBA") if img.mode in ("RGBA","LA","P") else img.convert("RGB")
        w,h = img.size
        thumb = img.resize(ThumbnailSize, Image.LANCZOS)
        thumb = thumb.quantize(colors=ThumbnailColors).convert("RGB")
        buf = io.BytesIO()
        thumb.save(buf, format="PNG", optimize=True)
        return w,h,buf.getvalue()

    def Encode(raw_bytes, filename):
        w,h,img_bytes = ProcessImage(raw_bytes)
        ext = filename.split(".")[-1].lower().encode("ascii")
        payload = (
            struct.pack(">B", len(ext)) +
            ext +
            struct.pack(Structure, w, h) +
            img_bytes
        )
        compressed = zlib.compress(payload, 9)
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")
        chunks = [encoded[i:i+ChunkSize] for i in range(0,len(encoded),ChunkSize)]
        lines = [f"{Header}|v1.0|meta|1|{len(chunks)}|0"]
        for i,c in enumerate(chunks):
            lines.append(f"{Header}|v1.0|chunk|{i}|{len(chunks)}|:{c}:")
        return "\\n".join(lines)

    def Decode(text):
        lines = text.split("\\n")
        meta = lines[0].split("|")
        total = int(meta[4])
        parts = [None]*total
        for l in lines[1:]:
            p = l.split("|")
            idx = int(p[3])
            parts[idx] = p[5][1:-1]
        data = "".join(parts)
        data += "=" * (-len(data) % 4)
        raw = base64.urlsafe_b64decode(data)
        raw = zlib.decompress(raw)
        ext_len = raw[0]
        ext = raw[1:1+ext_len].decode()
        rest = raw[1+ext_len:]
        w,h = struct.unpack(Structure, rest[:HeaderSize])
        img_data = rest[HeaderSize:]
        img = Image.open(io.BytesIO(img_data))
        img = img.resize((w,h), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="PNG", optimize=True)
        return base64.b64encode(out.getvalue()).decode("ascii")
    `);
}

async function encode() {
    const file = document.getElementById("file").files[0];
    if (!file) return;

    const buffer = await file.arrayBuffer();
    const bytes = new Uint8Array(buffer);

    pyodide.globals.set("js_bytes", bytes);
    pyodide.globals.set("js_filename", file.name);

    const result = await pyodide.runPythonAsync(`
raw = bytes(js_bytes)
Encode(raw, js_filename)
`);

    document.getElementById("out").value = result;
}

async function decode() {
    const text = document.getElementById("out").value;
    const result = await pyodide.runPythonAsync(`Decode("""${text}""")`);
    const img = document.getElementById("preview");
    if (!img) {
        console.error("preview element missing");
        return;
    }
    img.src = "data:image/png;base64," + result;
}

init();