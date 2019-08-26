export PATH=/usr/local/opt/ccache/libexec:$PATH

git fetch --tags

mkdir build
cd build
cmake -DCMAKE_OSX_DEPLOYMENT_TARGET=10.11 \
-DDepsPath=/tmp/obsdeps \
-DVLCPath=$PWD/../../vlc-3.0.4 \
-DENABLE_UI=false \
-DCOPIED_DEPENDENCIES=false \
-DCOPY_DEPENDENCIES=true \
-DENABLE_SCRIPTING=false ..

make -j4