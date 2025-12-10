#!/bin/bash
#
plugin_dir=$( basename $( pwd ) )
# Remove exists file and directory plugi
if [ -f "./$plugin_dir.zip" ]; then
  rm "./$plugin_dir.zip"
fi
if [ -d "./$plugin_dir" ]; then
  rm -r "./$plugin_dir"
fi
# Create Plugin Directory
mkdir "./$plugin_dir"
# Copy files
cp *.py "./$plugin_dir"
for item in __init__.py metadata.txt LICENSE; do cp "./$item" "./$plugin_dir"; done
cp -r ./tool "./$plugin_dir"
rm -r "./$plugin_dir/tool/__pycache__"
cp -r ./resources "./$plugin_dir"
# Create Translate files
mkdir "./$plugin_dir/i18n"
cp ./i18n/*.qm "./$plugin_dir/i18n"
# Create Zip and remove Plugin Directory
zip -q -r "$plugin_dir.zip" "./$plugin_dir"
rm -r "./$plugin_dir"
#
echo "Zip file created: "$plugin_dir".zip"
