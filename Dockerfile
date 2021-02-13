FROM balenalib/rpi-raspbian:buster-20201223 AS base

# Consider replacing ${USER} and ${GROUP} by the value of `whoami`
# Consider replacing $(UID) and ${GID} by the value of `id -u` and `id -g`
# This will create a user inside the docker image with the same characteristics as your local user.
ARG USER=pi
ARG GROUP=pi
ARG UID=1000
ARG GID=1000

RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y wget \
    htop \
    screen \
    tmux \
    software-properties-common \
    build-essential \
    gfortran \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libssl-dev \
    libreadline-dev \
    libffi-dev \
    libblas-dev \
    liblapack-dev \
    libopenblas-dev \
    libatlas-base-dev \
    libatlas3-base \
    libblis-dev

# Install project-specific packages
RUN apt-get install -y vlc \
    pulseaudio \
    libraspberrypi-bin

# Creating a "pi" user with UID 1000
RUN groupadd -g ${GID} ${GROUP} && useradd -u ${UID} -g ${GROUP} -s /bin/sh ${USER} && \
    usermod -a -G video ${USER} && \
    usermod -a -G video root

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
FROM base AS peoples-anthem

WORKDIR /app

# Compiling python from source
RUN cd /tmp && \
    wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz && \
    tar -xf Python-3.7.3.tgz && \
    cd Python-3.7.3 && \
    ./configure --enable-optimizations && \
    cd /app && \
    rm -rf /tmp/Python-3.7.3

RUN apt-get update && \
    apt-get install -y python3-dev python3-distutils python3-h5py

RUN curl --insecure https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

RUN python3 -m pip install pipenv==2020.11.15 scipy==1.5.4

# Installing PIL and opencv dependencies
# https://pillow.readthedocs.io/en/stable/installation.html
# https://blog.piwheels.org/new-opencv-builds/
RUN apt-get install -y libjpeg-dev \
    zlib1g-dev \
    libtiff5 \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl \
    libopenjp2-7-dev \
    libimagequant-dev \
    libraqm-dev \
    libxcb-xtest0-dev \
    libjasper1 \
    libharfbuzz0b \
    libwebp6 \
    libilmbase23 \
    libopenexr23 \
    libgstreamer1.0-0 \
    libavcodec58 \
    libavformat58 \
    libavutil56 \
    libswscale5 \
    libgtk-3-0 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libqtgui4 \
    libsz2 \
    libqt4-test \
    libqtcore4

# Download facenet model in expected directory as per:
# https://github.com/timesler/facenet-pytorch/blob/1d75625351cfa8f17591f271f2151ed9cb959f32/models/inception_resnet_v1.py#L333
ENV XDG_CACHE_HOME=/torch_models/.cache

# Downloading torch and torchvision .whl compiled for pi4
RUN mkdir --parents /home/${USER}/wheels && \
    mkdir --parents ${XDG_CACHE_HOME}/torch/checkpoints && \
    wget https://www.dropbox.com/s/015k4qyoofi6ld5/torch-1.6.0a0%2Bb31f58d-cp37-cp37m-linux_armv7l.whl?dl=0 -O /home/${USER}/wheels/torch-1.6.0a0+b31f58d-cp37-cp37m-linux_armv7l.whl && \
    wget https://www.dropbox.com/s/mmm5b0ovehujfz0/torchvision-0.7.0a0%2B78ed10c-cp37-cp37m-linux_armv7l.whl?dl=0 -O /home/${USER}/wheels/torchvision-0.7.0a0+78ed10c-cp37-cp37m-linux_armv7l.whl && \
    wget https://github.com/timesler/facenet-pytorch/releases/download/v2.2.9/20180402-114759-vggface2.pt -O ${XDG_CACHE_HOME}/torch/checkpoints/20180402-114759-vggface2.pt

COPY Pipfile Pipfile.lock .

RUN python3 -m pipenv install --dev --system --deploy

RUN rm -rf /home/${USER}/wheels/ Pipfile Pipfile.lock

USER ${USER}