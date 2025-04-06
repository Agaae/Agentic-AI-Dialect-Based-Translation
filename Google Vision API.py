from google.cloud import vision
import io

client = vision.ImageAnnotatorClient.from_service_account_file('apikey.json')

image_path = 'image1.jpg'

with io.open(image_path, 'rb') as image_file:
    content = image_file.read()
    
image = vision.Image(content=content)

response = client.text_detection(image=image)

texts = response.text_annotations
for text in texts:
    print(text.description, text.confidence)


# def print_text(response: vision.AnnotateImageResponse):
# /*************  ✨ Codeium Command ⭐  *************/
#     """
# /******  871f52c0-e71d-4372-af01-98da5534a786  *******/
#     print("=" * 80)
#     Each annotation includes the description of the detected text and the
#         vertices = [f"({v.x},{v.y})" for v in annotation.bounding_poly.vertices]
#         print(
#     Args:
#         response (vision.AnnotateImageResponse): The response object from the
#         Google Vision API containing text annotations.
#     """

#             ",".join(vertices),
#             sep=" | ",
#         )
        