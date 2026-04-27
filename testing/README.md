# pytest result
```bash
PS C:\Users\nelv\Documents\imext\testing> pytest test.py
================================================ test session starts ================================================
platform win32 -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\nelv\Documents\imext\testing
collected 10 items                                                                                                   

test.py ..........                                                                                             [100%]

================================================ 10 passed in 0.20s =================================================
PS C:\Users\nelv\Documents\imext\testing> 
```

# IMEXT Testing
This is the "pytest" test suite for IMEXT

## What it covers
It tests the functions inside ImageCodec (main.py) like Encode, Decode, ProcessImage.

## Test it yourself
Make sure you have `pytest` installed.
> ```pytest test.py```

This is automatic and doesn't require any other input after.