![](assets/banner.png)
<h1 align="center">IMEXT</h1>
Send compressed Images with Facebook's Free Data through Text

## What is IMEXT
IMEXT is a Bitmap Compressor, Encoder and a Decoder.

It is a proof of concept/working software that shows you can send Images with Facebook's Free Data through Text.

## Usage
```
python main.py encode [filename.type]
```

```
python main.py decode [filename_imext.txt]
```

or go to the website

## How it works
The `Payload` holds the raw binary data, but in a custom format.
> Payload is then encoded
> ```python
>Encoded = base64.urlsafe_b64encode(Payload).decode("ascii")
>```
>And is then put into multiple chunks.
> ```python
>Chunks = split(Encoded)
>```

The final structure would then be:
```
IMEXT|v1|chunk|...|DATA
```
DATA contains a chunk of the `base64` encoded payload string of that we talked about earlier, and embedded into the IMEXT Lines.

```python
Lines = [f"{Header}|v{Version}|meta|{int(UseCompression)}|{Total}|{CompressionRate}"]
        for Index, Chunk in enumerate(Chunks):
            Lines.append(f"{Header}|v{Version}|chunk|{Index + 1}|{Total}|:{Chunk}:")
```

Payload > Encoded string > split > Chunks > wrap > IMEXT encoded

Meta string: 
> name, version, instruction, usecompression (1 = true), total, compressionrate
>```
>IMEXT|v1.0|meta|1|37|88.26
>```

## Compression Rate
![](assets/comparison.png)

## The Vision
I was once outside minding my own business, when I wanted to send an Image to someone but I only had Free Data from Facebook.

Because of that I couldn't send the Image I wanted to send. This made me think for a very long time and the first examples that came up to my head was maybe storing every colors (RGB) into the text and decode it there, and the rest was history.