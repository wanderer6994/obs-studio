export PATH=/usr/local/opt/ccache/libexec:$PATH

git fetch --tags

mkdir build
cd build
cmake -DENABLE_SPARKLE_UPDATER=ON \
-DCMAKE_OSX_DEPLOYMENT_TARGET=10.11 \
-DDepsPath=/tmp/obsdeps \
-DVLCPath=$PWD/../../vlc-3.0.4 \
-DENABLE_UI=OFF \
-DCOPIED_DEPENDENCIES=OFF \
-DCOPY_DEPENDENCIES=ON \
-DENABLE_SCRIPTING=OFF ..

make -j4