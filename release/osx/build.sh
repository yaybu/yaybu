#!/bin/sh

APPNAME=Yaybu

TARGET=$APPNAME.app
MACOS=$TARGET/Contents/MacOS
RESOURCES=$TARGET/Contents/Resources

rm -rf $TARGET
mkdir -p $MACOS $RESOURCES

virtualenv -p /usr/local/Cellar/python/2.7.5/bin/python $RESOURCES
$RESOURCES/bin/pip install -e ../yaybu/src/yay
$RESOURCES/bin/pip install -e ../yaybu
virtualenv --relocatable $RESOURCES

cp Yaybu.icns $RESOURCES/Yaybu.icns

cat > $TARGET/Info.plist <<'EOF'
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
open -b com.apple.terminal $DIR/main
EOF
chmod 0755 $MACOS/$APPNAME

cat > $MACOS/main << 'EOF'
#! /bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
clear
$DIR/../Resources/bin/python -m yaybu.core.main
EOF
chmod 0755 $MACOS/main

