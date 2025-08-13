from PIL import Image

# Open the GIF file
gif_path = "download.gif"
gif = Image.open(gif_path)

# Display the first frame
gif.show()

# Iterate through all frames
frame_number = 1
try:
    while True:
        print(f"Displaying frame {frame_number}")
        gif.show()
        gif.seek(gif.tell() + 1)  # Move to the next frame
        frame_number += 1
except EOFError:
    print("End of GIF reached.")
