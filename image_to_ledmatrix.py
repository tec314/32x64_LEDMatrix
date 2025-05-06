from PIL import Image
import os

def extract_rgb_to_file(image_path, output_file, threshold):
    # Open the image
    img = Image.open(image_path)
    
    # Convert the image to RGBA (if it has an alpha channel for transparency)
    img = img.convert('RGBA')  # RGBA includes alpha for transparency

    # Get the size of the image
    width, height = img.size

    # Open the output file in write mode
    with open(output_file, 'w') as f:
        line_count = 0  # To keep track of how many values are written per line
        # Iterate through each pixel
        for y in range(height):
            for x in range(width):
                # Get the RGBA value of the pixel
                r, g, b, a = img.getpixel((x, y))

                # Calculate the sum of RGB values for sensitivity check
                color_sum = r + g + b

                # Check if the pixel is below the threshold and should be considered transparent
                if a < threshold:
                    hex_color = "0x000000"  # Set transparent pixels to blac
                else:
                    # Format the RGB value as 0xRRGGBB
                    hex_color = f"0x{r:02X}{g:02X}{b:02X}"

                # If not the first value in the line, add a comma
                if line_count > 0:
                    f.write(", ")

                # Write the hex color value
                f.write(hex_color)

                line_count += 1

                # After every 64 values, add a newline and reset the counter
                if line_count == 64:
                    f.write(",\n")  # Add a comma before the newline
                    line_count = 0

        # Ensure the final output ends with a newline if the last set of pixels was not 64
        if line_count != 0:
            f.write("\n")

# Example usage


current_dir = os.getcwd()
image_path = os.path.join(current_dir, 'image.png')  # Replace with your image file path
output_file = os.path.join(current_dir, 'output_rgb.txt')  # Output file for the RGB values
# Ask for the threshold value (default to 50)
try:
    threshold = int(input("Enter the color threshold (0-765, default 50): "))
except ValueError:
    threshold = 50  # Default value if input is invalid

extract_rgb_to_file(image_path, output_file, threshold)
print(f"RGB values have been written to {output_file}")
