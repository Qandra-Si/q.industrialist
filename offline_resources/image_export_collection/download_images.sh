#!/bin/bash
while read -r line; do
 line=$(echo $line)
 output="../../.q_industrialist/image_export_collection/Types/${line}_32.png"
 if [[ -f $output ]]; then
  echo "image ${line} exists"
 else
  echo "downloading image ${line}"
  curl http://imageserver.eveonline.com/Type/${line}_32.png --output $output
 fi
done < download_images.txt