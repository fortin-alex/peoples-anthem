CONTAINER_NAME=peoples_anthem
IMAGE_TAG=peoples-anthem

# The docker container will be run as the user (as opposed to ran as root)
USER_NAME=$(shell whoami)
UID=$(shell id -u)
GID=$(shell id -g)

# If XDG_RUNTIME_DIR is empty then default to /run/user/1000
# This means that, by default, we run as the user (as opposed to running as root)
ifeq ($(XDG_RUNTIME_DIR),)
XDG_RUNTIME_DIR := /run/user/1000
endif

# LOCAL_CODE_PATH will be mounted in the container at /app
# LOCAL_CODE_PATH points to where this repo is cloned locally
# LOCAL_MODEL_PATH points to where your trained face recognition model is saved locally
LOCAL_CODE_PATH=/home/$(USER_NAME)/projects/peoples-anthem
LOCAL_MODEL_PATH=/models

# Where the detected faces will be saved when building the dataset for training the face recognition algorithm
CONTAINER_DATASET_DIRECTORY=/app/data

.PHONY: build-peoples-anthem
build-peoples-anthem:
	DOCKER_BUILDKIT=1 docker build --target peoples-anthem -t $(IMAGE_TAG):latest .

# Launching docker container with devices needed to play music and read video from camera
# As per: https://stackoverflow.com/questions/28985714/run-apps-using-audio-in-a-docker-container
# AS per: https://www.losant.com/blog/how-to-access-the-raspberry-pi-camera-in-docker
PHONY: run-record-faces
run-record-faces:
	docker run -d --rm --privileged --name $(CONTAINER_NAME) --env XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR} --env LD_LIBRARY_PATH=/opt/vc/lib --device /dev/vchiq --device /dev/snd --device /dev/shm --device /etc/machine-id --volume /run/user:/run/user --volume /var/lib/dbus:/var/lib/dbus --volume ~/models-cache:/home/${USER_NAME}/models-cache --volume ~/.config/pulse:/home/${USER_NAME}/.config/pulse --volume /opt/vc:/opt/vc --volume /tmp/.X11-unix:/tmp/.X11-unix --volume $(LOCAL_MODEL_PATH):/models --volume $(LOCAL_CODE_PATH):/app $(IMAGE_TAG) bash -c "cd code && python3 build_dataset.py --path $(CONTAINER_DATASET_DIRECTORY)"

.PHONY: run-peoples-anthem
run-peoples-anthem:
	docker run -d --rm --privileged --name $(CONTAINER_NAME) --env XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR} --env LD_LIBRARY_PATH=/opt/vc/lib --device /dev/vchiq --device /dev/snd --device /dev/shm --device /etc/machine-id --volume /run/user:/run/user --volume /var/lib/dbus:/var/lib/dbus --volume ~/models-cache:/home/${USER_NAME}/models-cache --volume ~/.config/pulse:/home/${USER_NAME}/.config/pulse --volume /opt/vc:/opt/vc --volume /tmp/.X11-unix:/tmp/.X11-unix --volume $(LOCAL_MODEL_PATH):/models --volume $(LOCAL_CODE_PATH):/app $(IMAGE_TAG) bash -c "cd code && python3 recognize_and_play_music.py"

.PHONY: get-peoples-anthem-shell
run-peoples-anthem-shell:
	docker run -it --rm --privileged --name $(CONTAINER_NAME) --env XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR} --env LD_LIBRARY_PATH=/opt/vc/lib --device /dev/vchiq --device /dev/snd --device /dev/shm --device /etc/machine-id --volume /run/user:/run/user --volume /var/lib/dbus:/var/lib/dbus --volume ~/models-cache:/home/${USER_NAME}/models-cache --volume ~/.config/pulse:/home/${USER_NAME}/.config/pulse --volume /opt/vc:/opt/vc --volume /tmp/.X11-unix:/tmp/.X11-unix --volume $(LOCAL_MODEL_PATH):/models --volume $(LOCAL_CODE_PATH):/app $(IMAGE_TAG)
