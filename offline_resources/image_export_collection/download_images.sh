#!/bin/bash
while read -r line; do
 line=$(echo $line)
 curl http://imageserver.eveonline.com/Type/${line}_32.png --output ../../.q_industrialist/image_export_collection/Types/${line}_32.png
done < download_images.txt