IMAGE_TAG=peoples-anthem
IMAGE_TAG_VIDEO_RECORDER=video-recorder

.PHONY: build-model-trainer
build-model-trainer:
	DOCKER_BUILDKIT=1 docker build --target model-trainer -t $(IMAGE_TAG):latest .

.PHONY: build-video-recorder
build-video-recorder:
	DOCKER_BUILDKIT=1 docker build --target video-recorder -t $(IMAGE_TAG_VIDEO_RECORDER):latest .

.PHONY: get-shell
get-shell:
	docker run -it --rm --privileged --entrypoint /bin/bash $(IMAGE_TAG):latest

VIDEO_RECORDER_CONTAINER_NAME=video_recorder
RUN_COMMAND=/bin/bash -c "cd ./pikrellcam; { echo '1234'; echo 'yes'; echo 'no'; } | ./install-pikrellcam.sh; sudo /etc/init.d/php7.3-fpm start; sudo service nginx start; tail -f /dev/null"

.PHONY: run-video-recorder
run-video-recorder:
	docker run -it -d --rm --privileged -p 1234:1234 --name $(VIDEO_RECORDER_CONTAINER_NAME) --env LD_LIBRARY_PATH=/opt/vc/lib --device /dev/vchiq --device /dev/snd --device /dev/shm --device /etc/machine-id --volume /run/user:/run/user --volume /var/lib/dbus:/var/lib/dbus --volume /opt/vc:/opt/vc --volume /tmp/.X11-unix:/tmp/.X11-unix $(IMAGE_TAG_VIDEO_RECORDER):latest $(RUN_COMMAND)

CONTAINER_NAME=peoples_anthem
CODE_PATH=/home/pi/projects/peoples-anthem
DATASET_DIRECTORY=/app/data
MODEL_PATH=/models
USER_NAME=$(shell whoami)
UID=$(shell id -u)
GID=$(shell id -g)

# If XDG_RUNTIME_DIR is empty then default to /run/user/0
# This is useful when running this make command from a cron job.
ifeq ($(XDG_RUNTIME_DIR),)
XDG_RUNTIME_DIR := /run/user/1000
endif


.PHONY: print-uid
print-uid:
	@echo ${UID}
	@echo ${XDG_RUNTIME_DIR}
	@echo ${USER_NAME}

# Launching docker container with devices needed to play music and read video from camera
# As per: https://stackoverflow.com/questions/28985714/run-apps-using-audio-in-a-docker-container
# AS per: https://www.losant.com/blog/how-to-access-the-raspberry-pi-camera-in-docker
.PHONY: run-peoples-anthem-shell
run-peoples-anthem-shell:
	docker run -it --rm --privileged --name $(CONTAINER_NAME) --env XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR} --env LD_LIBRARY_PATH=/opt/vc/lib --device /dev/vchiq --device /dev/snd --device /dev/shm --device /etc/machine-id --volume /run/user:/run/user --volume /var/lib/dbus:/var/lib/dbus --volume ~/models-cache:/home/${USER_NAME}/models-cache --volume ~/.config/pulse:/home/${USER_NAME}/.config/pulse --volume /opt/vc:/opt/vc --volume /tmp/.X11-unix:/tmp/.X11-unix --volume $(MODEL_PATH):/models --volume $(CODE_PATH):/app $(IMAGE_TAG)

.PHONY: run-peoples-anthem
run-peoples-anthem:
	docker run -d --rm --privileged --name $(CONTAINER_NAME) --env XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR} --env LD_LIBRARY_PATH=/opt/vc/lib --device /dev/vchiq --device /dev/snd --device /dev/shm --device /etc/machine-id --volume /run/user:/run/user --volume /var/lib/dbus:/var/lib/dbus --volume ~/models-cache:/home/${USER_NAME}/models-cache --volume ~/.config/pulse:/home/${USER_NAME}/.config/pulse --volume /opt/vc:/opt/vc --volume /tmp/.X11-unix:/tmp/.X11-unix --volume $(MODEL_PATH):/models --volume $(CODE_PATH):/app $(IMAGE_TAG) bash -c "cd code && python3 recognize_and_play_music.py"

PHONY: run-record-faces
run-record-faces:
	docker run -d --rm --privileged --name $(CONTAINER_NAME) --env XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR} --env LD_LIBRARY_PATH=/opt/vc/lib --device /dev/vchiq --device /dev/snd --device /dev/shm --device /etc/machine-id --volume /run/user:/run/user --volume /var/lib/dbus:/var/lib/dbus --volume ~/models-cache:/home/${USER_NAME}/models-cache --volume ~/.config/pulse:/home/${USER_NAME}/.config/pulse --volume /opt/vc:/opt/vc --volume /tmp/.X11-unix:/tmp/.X11-unix --volume $(MODEL_PATH):/models --volume $(CODE_PATH):/app $(IMAGE_TAG) bash -c "cd code && python3 build_dataset.py --path $(DATASET_DIRECTORY)"



#-v /dev/shm:/dev/shm \
    -v /etc/machine-id:/etc/machine-id \
    -v /run/user/$uid/pulse:/run/user/$uid/pulse \
    -v /var/lib/dbus:/var/lib/dbus \
    -v ~/.pulse:/home/$dockerUsername/.pulse