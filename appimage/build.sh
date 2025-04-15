#!/bin/bash -xe

this_script="$( readlink -f "$0" )"
this_dir="${this_script%/*}"
hyperapp_dir="${this_dir%/*}"

work_dir="/tmp/hyperapp-image"

target_image_name=hyperapp-python3.11.12-cp311-cp311-manylinux2014_x86_64.AppImage
python_image_name=python3.11.12-cp311-cp311-manylinux2014_x86_64.AppImage
appimagetool_image_name=appimagetool-x86_64.AppImage

target_image_path="$work_dir/$target_image_name"
appimagetool_image_path="$work_dir/$appimagetool_image_name"
python_image_path="$work_dir/$python_image_name"

mkdir -p "$work_dir"

if [ ! -x "$appimagetool_image_path" ]; then
  rm -rf "$work_dir/*"
  wget "https://github.com/AppImage/AppImageKit/releases/download/continuous/$appimagetool_image_name" --output-document="$appimagetool_image_path"
  chmod +x "$appimagetool_image_path"
fi

if [ ! -x "$python_image_path" ]; then
  rm -rf "$work_dir/*"
  wget "https://github.com/niess/python-appimage/releases/download/python3.11/$python_image_name" --output-document="$python_image_path"
  chmod +x "$python_image_path"
fi

python_fs="$work_dir/python-fs"
target_fs="$work_dir/hyperapp-fs"

if [ ! -d "$python_fs" ]; then
  pushd "$( dirname "$python_fs" )"
  "$python_image_path" --appimage-extract
  mv squashfs-root "$( basename "$python_fs" )"
  popd
fi

if [ ! -d "$target_fs" ]; then
  cp -r "$python_fs" "$target_fs"
  mv "$target_fs/AppRun" "$target_fs/python"
  # Original python appdata does not work for us. We do not need it anyway.
  rm -r "$target_fs/usr/share/metainfo/python3.11.12.appdata.xml"
fi

"$target_fs/python" --version
"$target_fs/python" -m pip install -r "$hyperapp_dir/requirements.txt"

rsync -a \
      --exclude .git \
      --exclude .cache \
      --exclude .pytest_cache \
      --exclude .idea \
      --exclude __pycache__ \
      --exclude TAGS \
      --exclude prof \
      --exclude ipython-profile \
      "$hyperapp_dir" "$target_fs/"
cp "$this_dir/AppRun" "$target_fs/"

"$appimagetool_image_path" "$target_fs" "$target_image_path"
