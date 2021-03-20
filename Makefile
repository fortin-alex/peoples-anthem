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
LOCAL_CODE_PATH=$(shell pwd)
LOCAL_MODEL_PATH=$(LOCAL_CODE_PATH)/models

# Where the detected faces will be saved when building the dataset for training the face recognition algorithm
CONTAINER_CODE_PATH=/app
CONTAINER_DATASET_DIRECTORY=$(CONTAINER_CODE_PATH)/data

CONTAINER_MODEL_PATH=$(CONTAINER_CODE_PATH)/models
CONTAINER_MODEL_FILENAME=model.v1.pklz
CONTAINER_MODEL_FILEPATH=$(CONTAINER_MODEL_PATH)/$(CONTAINER_MODEL_FILENAME)

.PHONY: mkdir-model-path-if-not-exists
mkdir-model-path-if-not-exists:
	if [ ! -d $(LOCAL_MODEL_PATH) ]; then mkdir -p $(LOCAL_MODEL_PATH); fi

.PHONY: check-if-model-is-trained
check-if-model-is-trained:
	if [ ! -f $(LOCAL_MODEL_PATH)/$(CONTAINER_MODEL_FILENAME) ]; then echo "Your model: $(LOCAL_CODE_PATH)/$(CONTAINER_MODEL_FILENAME) does not exist locally"; false ; fi

.PHONY: build-peoples-anthem
build-peoples-anthem:
	DOCKER_BUILDKIT=1 docker build --target peoples-anthem -t $(IMAGE_TAG):latest .

# Launching docker container with devices needed to play music and read video from camera
# As per: https://stackoverflow.com/questions/28985714/run-apps-using-audio-in-a-docker-container
# AS per: https://www.losant.com/blog/how-to-access-the-raspberry-pi-camera-in-docker
PHONY: run-record-faces
run-record-faces: mkdir-model-path-if-not-exists
	docker run \
	-d \
	--rm \
	--privileged \
	--name $(CONTAINER_NAME) \
	--env XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR} \
	--env LD_LIBRARY_PATH=/opt/vc/lib \
	--device /dev/vchiq \
	--device /dev/snd \
	--device /dev/shm \
	--device /etc/machine-id \
	--volume /run/user:/run/user \
	--volume /var/lib/dbus:/var/lib/dbus \
	--volume ~/.config/pulse:/home/${USER_NAME}/.config/pulse \
	--volume /opt/vc:/opt/vc \
	--volume /tmp/.X11-unix:/tmp/.X11-unix \
	--volume $(LOCAL_MODEL_PATH):/models \
	--volume $(LOCAL_CODE_PATH):$(CONTAINER_CODE_PATH) \
	$(IMAGE_TAG) \
	bash -c "cd code && python3 build_dataset.py --model-filepath $(CONTAINER_MODEL_FILEPATH) --path $(CONTAINER_DATASET_DIRECTORY)"

PHONY: train-model
train-model: mkdir-model-path-if-not-exists
	docker run \
	-it \
	--rm \
	--name $(CONTAINER_NAME) \
	--volume $(LOCAL_MODEL_PATH):$(CONTAINER_MODEL_PATH) \
	--volume $(LOCAL_CODE_PATH):$(CONTAINER_CODE_PATH) \
	$(IMAGE_TAG) \
	/bin/bash -c "cd code && python3 train_face_recognition.py --input-path $(CONTAINER_DATASET_DIRECTORY) --output-filepath $(CONTAINER_MODEL_FILEPATH)"

.PHONY: run-peoples-anthem
run-peoples-anthem: check-if-model-is-trained mkdir-model-path-if-not-exists
	docker run \
	-d \
	--rm \
	--privileged \
	--name $(CONTAINER_NAME) \
	--env XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR} \
	--env LD_LIBRARY_PATH=/opt/vc/lib \
	--device /dev/vchiq \
	--device /dev/snd \
	--device /dev/shm \
	--device /etc/machine-id \
	--volume /run/user:/run/user \
	--volume /var/lib/dbus:/var/lib/dbus \
	--volume ~/.config/pulse:/home/${USER_NAME}/.config/pulse \
	--volume /opt/vc:/opt/vc \
	--volume /tmp/.X11-unix:/tmp/.X11-unix \
	--volume $(LOCAL_MODEL_PATH):$(CONTAINER_MODEL_PATH) \
	--volume $(LOCAL_CODE_PATH):$(CONTAINER_CODE_PATH) \
	$(IMAGE_TAG) \
	bash -c "cd code && python3 recognize_and_play_music.py --model-filepath $(CONTAINER_MODEL_FILEPATH)"

.PHONY: get-peoples-anthem-shell
get-peoples-anthem-shell: mkdir-model-path-if-not-exists
	docker run \
	-it \
	--rm \
	--privileged \
	--name $(CONTAINER_NAME) \
	--env XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR} \
	--env LD_LIBRARY_PATH=/opt/vc/lib \
	--device /dev/vchiq \
	--device /dev/snd \
	--device /dev/shm \
	--device /etc/machine-id \
	--volume /run/user:/run/user \
	--volume /var/lib/dbus:/var/lib/dbus \
	--volume ~/.config/pulse:/home/${USER_NAME}/.config/pulse \
	--volume /opt/vc:/opt/vc \
	--volume /tmp/.X11-unix:/tmp/.X11-unix \
	--volume $(LOCAL_MODEL_PATH):$(CONTAINER_MODEL_PATH) \
	--volume $(LOCAL_CODE_PATH):$(CONTAINER_CODE_PATH) \
	$(IMAGE_TAG) \
	/bin/bash
