# Crop images
convert output/*.png -crop 850x686+50x1 output/cropped.png

# Create video
ffmpeg -framerate 5 -pattern_type glob -i 'output/cropped-*.png' \
  -c:v libx264 -r 5 -pix_fmt yuv420p output/tempsAnim.mp4

# Delete cropped images
rm output/cropped-*