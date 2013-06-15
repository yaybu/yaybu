#!/bin/bash

APPNAME=Yaybu
VERSION=0.3.0

PYTHON_VERSION=2.7.5

TARGET=$APPNAME.app
CONTENTS=$TARGET/Contents
MACOS=$CONTENTS/MacOS
RESOURCES=$CONTENTS/Resources

CACHE_DIR=$(pwd)/cache

rm -rf $TARGET
mkdir -p $MACOS $RESOURCES


FRAMEWORK_PATH=$(python -c "print __import__('sys').exec_prefix[:sys.exec_prefix.find('Python.framework')+len('Python.framework')]")
FRAMEWORK_VERSION=$(python -c "print __import__('sys').version[:3]")
FRAMEWORK_SRC=$FRAMEWORK_PATH/Versions/$FRAMEWORK_VERSION
FRAMEWORK_DST=$CONTENTS/Frameworks/Python.framework/Versions/$FRAMEWORK_VERSION

mkdir -p $FRAMEWORK_DST/Resources
cp $FRAMEWORK_SRC/Python $FRAMEWORK_DST/Python
cp $FRAMEWORK_SRC/Resources/English.lproj $FRAMEWORK_DST/Resources/English.lproj
cp $FRAMEWORK_SRC/Resources/Info.plist $FRAMEWORK_DST/Resources/Info.plist
cp $FRAMEWORK_SRC/Resources/version.plist $FRAMEWORK_DST/version.plist


#virtualenv -p /usr/local/Cellar/python/2.7.5/bin/python $RESOURCES
virtualenv $RESOURCES
$RESOURCES/bin/pip install --download-cache $CACHE_DIR -e ../../src/yay
$RESOURCES/bin/pip install --download-cache $CACHE_DIR -e ../..
virtualenv --relocatable $RESOURCES

cp Yaybu.icns $RESOURCES/Yaybu.icns

cat > $CONTENTS/Info.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>CFBundleExecutable</key>
        <string>Yaybu</string>
        <key>CFBundleIconFile</key>
        <string>Yaybu.icns</string>
        <key>CFBundleInfoDictionaryVersion</key>
        <string>1.0</string>
        <key>CFBundlePackageType</key>
        <string>APPL</string>
        <key>CFBundleSignature</key>
        <string>????</string>
        <key>CFBundleVersion</key>
        <string>1.0</string>
    </dict>
</plist>
EOF

cat > $MACOS/$APPNAME <<'EOF'
#! /bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# exec /Applications/Utilities/Terminal.app/Contents/MacOS/Terminal $DIR/main
open -b com.apple.terminal $DIR/main
EOF
chmod 0755 $MACOS/$APPNAME

cat > $MACOS/main << 'EOF'
#! /bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
printf '\e]1;Yaybu\a'
clear
$DIR/../Resources/bin/python -m yaybu.core.main
EOF
chmod 0755 $MACOS/main

./pkg-dmg \
    --idme \
    --volname "$APPNAME" \
    --source $TARGET \
    --sourcefile \
    --symlink /Applications:Applications \
    --target "$APPNAME-$VERSION.dmg" \
    --icon Yaybu.icns \
    --copy DS_Store:.DS_Store
    #--mkdir .background \
    #--copy background.png:.background/background.png \
    # --attribute V:.background

