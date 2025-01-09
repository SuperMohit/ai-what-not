import base64
from openai import OpenAI


from pdf2image import convert_from_path
import os

client = OpenAI()

# Path to the PDF file
pdf_path = '/Users/mohit/Downloads/CCCV_rate_sheet_2019-20190605_10224792.pdf'

# Output directory
output_dir = '/Users/mohit/Downloads/output_images_final'


def convert_pdf_to_images(pdf_path, output_dir):
    """
    Converts a PDF file into separate image files for each page and saves them in the specified output directory.

    Args:
    - pdf_path (str): The path to the PDF file to be converted.
    - output_dir (str): The directory where the image files will be saved. If it doesn't exist, it will be created.

    The function uses a DPI of 300 for image conversion and saves each page as a PNG file with filenames in the format 'page_<page_number>.png'.
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Convert the PDF to images
    images = convert_from_path(pdf_path, dpi=300)

    # Save each page as an image
    for i, image in enumerate(images):
        # Define the output filename
        output_filename = os.path.join(output_dir, f'page_{i + 1}.png')
        # Save the image
        image.save(output_filename, 'PNG')

    print(f"Successfully converted '{pdf_path}' to images in '{output_dir}' directory.")


# Function to encode the image
def encode_image(image_path):
    """
    Encodes an image file to a base64 string.

    Args:
    - image_path (str): The path to the image file to be encoded.

    Returns:
    - str: The base64 encoded string of the image content.

    This function reads the image file in binary mode and converts its content
    to a base64 encoded string. The output can be used for embedding image data
    in text-based formats like JSON or HTML.
    """

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")



def process_directory(directory_path):
    """
    Processes all image files in a directory by extracting tables from them
    using the OpenAI API and printing the results as CSV.

    Args:
        directory_path (str): The path to the directory containing the image files.

    This function iterates over all files in the directory, encodes each image
    file to a base64 string, and then calls process_image to extract the table
    from the image and print the result as CSV.
    """
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            base64_image = encode_image(file_path)
            process_image(base64_image)




def process_image(base64_image):
    """
    Processes a base64 encoded image to extract tabular data using the OpenAI API.

    Args:
        base64_image (str): The base64 encoded string of the image.

    This function sends a request to the OpenAI API with the base64 encoded image
    and prompts it to extract any tabular data present in the image. The response
    is expected to be in CSV format, which is printed to the console.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract table from the image return in csv format. Only return csv, nothing else",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )

    print(response.choices[0].message.content)   


if __name__ == "__main__":
    convert_pdf_to_images(pdf_path, output_dir)
    process_directory(output_dir)
