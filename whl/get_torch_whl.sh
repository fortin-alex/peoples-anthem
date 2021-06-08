git clone https://github.com/pytorch/pytorch --recursive && cd pytorch
cd pytorch
git checkout v1.6.0 # optional, you can build master if you are brave
git submodule update --init --recursive


export NO_CUDA=1
export NO_DISTRIBUTED=1
export NO_MKLDNN=1 
export BUILD_TEST=0 # for faster builds
export MAX_JOBS=3
# export NO_NNPACK=1
# export NO_QNNPACK=1

python3 setup.py bdist_wheel

