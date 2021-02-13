# Peoples Anthem

<div align="center">
  <img src="https://www.tensorflow.org/images/tf_logo_social.png">
</div>

A project using face recognition and a raspberry pi's webcam to identify a person and play their favorite music

People's anthem allows its user to play sounds or music from a Raspberry pi when a person walks in front of a webcam attached to the raspberri pi.

## Requierements
You will need:
* A [raspberri pi](https://www.raspberrypi.org/)
* Docker installed on your OS ([how to install](https://docs.docker.com/engine/install/debian/))
* A [raspberri pi webcam](https://www.raspberrypi.org/products/camera-module-v2/)
* A speaker connected to your audio jack
* A source of music (mp3 or a Spotify account)


## Install


## Usage
Once you have a trained `face recognition model` and that your `./code/config.py` is set up, you can run `people's anthem` with this command:

```
make run-peoples-anthem
```


## License

[GPLv3](LICENSE)