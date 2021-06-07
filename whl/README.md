# whl
In this section of the repo, we put scripts used to build `torch` and `torchvision` wheel file on `rpi4`.
This is also the directory where these `.whl` must be kept after they are built.

## Notes
The wheels can be downloaded like so:

```bash
wget https://www.dropbox.com/s/015k4qyoofi6ld5/torch-1.6.0a0%2Bb31f58d-cp37-cp37m-linux_armv7l.whl?dl=0 -O ./torch-1.6.0a0+b31f58d-cp37-cp37m-linux_armv7l.whl
wget https://www.dropbox.com/s/mmm5b0ovehujfz0/torchvision-0.7.0a0%2B78ed10c-cp37-cp37m-linux_armv7l.whl?dl=0 -O ./torchvision-0.7.0a0+78ed10c-cp37-cp37m-linux_armv7l.whl
```