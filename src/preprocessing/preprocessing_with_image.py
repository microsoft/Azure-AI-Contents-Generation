import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import ContentFormat
from openai import AzureOpenAI
from PIL import Image
import fitz  # PyMuPDF
import mimetypes
import base64
from mimetypes import guess_type

from preprocessing.preprocessing import convert_markdown_headings

# Load environment variables
load_dotenv()

MAX_TOKENS = 2000

def crop_image_from_image(image_path, page_number, bounding_box):
    """
    Crop an image from a TIFF file based on the bounding box.

    Args:
        image_path (str): The path to the image file.
        page_number (int): The page number of the image (used for multi-page TIFF).
        bounding_box (tuple): The bounding box coordinates (left, top, right, bottom).

    Returns:
        Image: The cropped image.
    """
    with Image.open(image_path) as img:
        if img.format == "TIFF":
            img.seek(page_number)
            img = img.copy()
        cropped_image = img.crop(bounding_box)
        return cropped_image

def crop_image_from_pdf_page(pdf_path, page_number, bounding_box):
    """
    Crop an image from a PDF page based on the bounding box.

    Args:
        pdf_path (str): The path to the PDF file.
        page_number (int): The page number to crop from.
        bounding_box (tuple): The bounding box coordinates (left, top, right, bottom).

    Returns:
        Image: The cropped image.
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)
    bbx = [x * 72 for x in bounding_box]
    rect = fitz.Rect(bbx)
    pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72), clip=rect)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img

def crop_image_from_file(file_path, page_number, bounding_box):
    """
    Crop an image from a file (PDF or image) based on the bounding box.

    Args:
        file_path (str): The path to the file.
        page_number (int): The page number to crop from (for PDF or multi-page TIFF).
        bounding_box (tuple): The bounding box coordinates (left, top, right, bottom).

    Returns:
        Image: The cropped image.
    """
    mime_type = mimetypes.guess_type(file_path)[0]
    if mime_type == "application/pdf":
        return crop_image_from_pdf_page(file_path, page_number, bounding_box)
    else:
        return crop_image_from_image(file_path, page_number, bounding_box)

def local_image_to_data_url(image_path):
    """
    Convert a local image file to a data URL.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The data URL of the image.
    """
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:{mime_type};base64,{base64_encoded_data}"

def understand_image_with_gpt(api_base, api_key, deployment_name, api_version, image_path, caption):
    """
    Use multimodal GPT(4V, 4o) to understand and describe an image.

    Args:
        api_base (str): The base URL of the Azure OpenAI service.
        api_key (str): The API key for the Azure OpenAI service.
        deployment_name (str): The deployment name for the GPT-4V model.
        api_version (str): The API version for the Azure OpenAI service.
        image_path (str): The path to the image file.
        caption (str): The caption for the image (if any).

    Returns:
        str: The description of the image generated by GPT-4V.
    """
    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        base_url=f"{api_base}/openai/deployments/{deployment_name}"
    )
    data_url = local_image_to_data_url(image_path)
    messages = [
        { "role": "system", "content": "You are a helpful assistant." },
        { "role": "user", "content": [
            { "type": "text", "text": f"Describe this image (note: it has image caption: {caption}):" } if caption else { "type": "text", "text": "Describe this image:" },
            { "type": "image_url", "image_url": { "url": data_url } }
        ]}
    ]

    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        max_tokens=MAX_TOKENS
    )

    return response.choices[0].message.content

def update_figure_description(md_content, img_description, idx):
    """
    Update the markdown content with the new figure description.

    Args:
        md_content (str): The original markdown content.
        img_description (str): The description of the image.
        idx (int): The index of the figure.

    Returns:
        str: The updated markdown content with the figure description.
    """
    start_substring = f"![](figures/{idx})"
    end_substring = "</figure>"
    new_string = f"<!-- FigureContent=\"{img_description}\" -->"
    start_index = md_content.find(start_substring)
    if start_index != -1:
        start_index += len(start_substring)
        end_index = md_content.find(end_substring, start_index)
        if end_index != -1:
            md_content = md_content[:start_index] + new_string + md_content[end_index:]
    return md_content

def analyze_layout(input_file_path, output_folder, doc_intelligence_endpoint, doc_intelligence_key, aoai_api_base, aoai_api_key, aoai_deployment_name, aoai_api_version):
    """
    Analyze the layout of a document and extract figures along with their descriptions.

    Args:
        input_file_path (str): The path to the input document file.
        output_folder (str): The path to the output folder where cropped images will be saved.
        doc_intelligence_endpoint (str): The endpoint for the Azure Document Intelligence API.
        doc_intelligence_key (str): The key for the Azure Document Intelligence API.
        aoai_api_base (str): The base URL of the Azure OpenAI service.
        aoai_api_key (str): The API key for the Azure OpenAI service.
        aoai_deployment_name (str): The deployment name for the GPT-4V model.
        aoai_api_version (str): The API version for the Azure OpenAI service.

    Returns:
        str: The updated markdown content with figure descriptions.
    """
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=doc_intelligence_endpoint,
        credential=AzureKeyCredential(doc_intelligence_key),
        headers={"x-ms-useragent": "sample-code-figure-understanding/1.0.0"},
    )
    with open(input_file_path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout", analyze_request=f, content_type="application/octet-stream", output_content_format=ContentFormat.MARKDOWN
        )
    result = poller.result()
    md_content = result.content

    if result.figures:
        print("Figures:")
        for idx, figure in enumerate(result.figures):
            figure_content = ""
            img_description = ""
            print(f"Figure #{idx} has the following spans: {figure.spans}")
            for i, span in enumerate(figure.spans):
                print(f"Span #{i}: {span}")
                figure_content += md_content[span.offset:span.offset + span.length]
            print(f"Original figure content in markdown: {figure_content}")

            if figure.caption:
                caption_region = figure.caption.bounding_regions
                print(f"\tCaption: {figure.caption.content}")
                print(f"\tCaption bounding region: {caption_region}")
                for region in figure.bounding_regions:
                    if region not in caption_region:
                        print(f"\tFigure body bounding regions: {region}")
                        boundingbox = (
                            region.polygon[0],  # x0 (left)
                            region.polygon[1],  # y0 (top)
                            region.polygon[4],  # x1 (right)
                            region.polygon[5]   # y1 (bottom)
                        )
                        print(f"\tFigure body bounding box in (x0, y0, x1, y1): {boundingbox}")
                        cropped_image = crop_image_from_file(input_file_path, region.page_number - 1, boundingbox)
                        base_name = os.path.basename(input_file_path)
                        file_name_without_extension = os.path.splitext(base_name)[0]
                        output_file = f"{file_name_without_extension}_cropped_image_{idx}.png"
                        cropped_image_filename = os.path.join(output_folder, output_file)
                        cropped_image.save(cropped_image_filename)
                        print(f"\tFigure {idx} cropped and saved as {cropped_image_filename}")
                        img_description += understand_image_with_gpt(aoai_api_base, aoai_api_key, aoai_deployment_name, aoai_api_version, cropped_image_filename, figure.caption.content)
                        print(f"\tDescription of figure {idx}: {img_description}")
            else:
                print("\tNo caption found for this figure.")
                for region in figure.bounding_regions:
                    print(f"\tFigure body bounding regions: {region}")
                    boundingbox = (
                        region.polygon[0],  # x0 (left)
                        region.polygon[1],  # y0 (top
                        region.polygon[4],  # x1 (right)
                        region.polygon[5]   # y1 (bottom)
                    )
                    print(f"\tFigure body bounding box in (x0, y0, x1, y1): {boundingbox}")
                    cropped_image = crop_image_from_file(input_file_path, region.page_number - 1, boundingbox)
                    base_name = os.path.basename(input_file_path)
                    file_name_without_extension = os.path.splitext(base_name)[0]
                    output_file = f"{file_name_without_extension}_cropped_image_{idx}.png"
                    cropped_image_filename = os.path.join(output_folder, output_file)
                    cropped_image.save(cropped_image_filename)
                    print(f"\tFigure {idx} cropped and saved as {cropped_image_filename}")
                    img_description += understand_image_with_gpt(aoai_api_base, aoai_api_key, aoai_deployment_name, aoai_api_version, cropped_image_filename, "")
                    print(f"\tDescription of figure {idx}: {img_description}")

            md_content = update_figure_description(md_content, img_description, idx)

    md_content_return = convert_markdown_headings(md_content)
    
    return md_content_return
