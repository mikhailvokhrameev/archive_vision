from pathlib import Path
from PIL import ImageFilter, ImageEnhance, Image
from scipy import ndimage
from scipy.signal import find_peaks
import os
import torch
import numpy as np
import cv2
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from pdf2image import convert_from_path
from tqdm import tqdm


def preprocess_for_segmentation(image):
    print(f" preprocess_for_segmentation started")
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)
    image = image.filter(ImageFilter.GaussianBlur(radius=0.3))
    image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=50, threshold=3))
    print(f" preprocess_for_segmentation finished")
    return image

def binarize_image(image, method='sauvola'):
    print(f" binarize_image started")
    if image.mode != 'L':
        grayscale_image = image.convert('L')
    else:
        grayscale_image = image
    img_array = np.array(grayscale_image)
    if method == 'otsu':
        _, binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == 'adaptive':
        binary = cv2.adaptiveThreshold(img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
    elif method == 'sauvola':
        window_size = 25
        k = 0.2
        mean = cv2.boxFilter(img_array.astype(np.float32), -1, (window_size, window_size))
        sqmean = cv2.boxFilter((img_array.astype(np.float32))**2, -1, (window_size, window_size))
        variance = sqmean - mean**2
        std = np.sqrt(variance)
        threshold = mean * (1 + k * ((std / 128) - 1))
        binary = np.where(img_array > threshold, 255, 0).astype(np.uint8)
    else:
        _, binary = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY)
    print(f" binarize_image finished")
    return Image.fromarray(binary)

def segment_lines_projection(image, min_line_height=10):
    print(f"segment_lines_projection started")
    try:
        processed_img = preprocess_for_segmentation(image)
        binary_img = binarize_image(processed_img, method='sauvola')
        img_array = np.array(binary_img)
        if np.mean(img_array) < 127:
            img_array = 255 - img_array
        horizontal_projection = np.sum(img_array == 0, axis=1)
        smoothed_projection = ndimage.gaussian_filter1d(horizontal_projection, sigma=1)
        inverted_projection = np.max(smoothed_projection) - smoothed_projection
        gaps, _ = find_peaks(inverted_projection, height=np.max(inverted_projection) * 0.5, distance=min_line_height)
        line_boundaries = [0] + list(gaps) + [len(horizontal_projection)]
        for i in range(len(line_boundaries) - 1):
            start = line_boundaries[i]
            end = line_boundaries[i + 1]
            region_projection = smoothed_projection[start:end]
            if np.max(region_projection) < np.max(smoothed_projection) * 0.1:
                continue
            text_rows = region_projection > np.max(region_projection) * 0.1
            text_indices = np.where(text_rows)[0]
            if len(text_indices) == 0:
                continue
            actual_start = start + text_indices[0] - 2
            actual_end = start + text_indices[-1] + 2
            actual_start = max(0, actual_start)
            actual_end = min(image.height, actual_end)
            if actual_end - actual_start < min_line_height:
                continue
            yield (0, actual_start, image.width, actual_end)
    except Exception as e:
        print(f"Projection segmentation failed: {e}")
    print(f"segment_lines_projection finished")

def segment_lines(image, methods=['projection'], min_line_height=10):
    print(f"segment_lines started")
    if isinstance(image, (str, Path)):
        image = Image.open(image)
    all_line_coords = []
    for method in methods:
        if method == 'projection':
            line_coords = list(segment_lines_projection(image, min_line_height))
            if line_coords:
                all_line_coords.extend(line_coords)
                break
        else:
            print(f"Unknown method: {method}")
            continue
    print(f"segment_lines finished")
    return all_line_coords

def split_double_page(image: Image.Image):
    w, h = image.size
    mid = w // 2
    left = image.crop((0, 0, mid, h))
    right = image.crop((mid, 0, w, h))
    return left, right

def preprocess_image(img):
    if img is None:
        return None
    if len(img.shape) == 3:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        return pil_img
    else:  # Grayscale
        gray = img.copy()
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        result = cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
        return Image.fromarray(result)

def process_single_file(file_path, output_folder_preprocessed, file_index=1, min_line_height=50):
    print(f" Processing: {file_path.name}")
    results = []
    try:
        if file_path.suffix.lower() == '.pdf':
            pages = convert_from_path(str(file_path), dpi=400)
            for page_idx, page in enumerate(pages):
                img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
                # further processing can be inserted here
        else:
            img = cv2.imread(str(file_path))
            if img is None:
                raise IOError(f"Cannot read image file: {file_path}")

        processed = preprocess_image(img)
        if processed is not None:
            left, right = split_double_page(processed)
            for page_img, page_side in tqdm([(left, 'left'), (right, 'right')], desc='processing_img'):
                page_path = Path(output_folder_preprocessed) / f"{file_path.stem}_f{file_index:02d}_{page_side}.tif"
                page_img.save(str(page_path))
                line_coords = segment_lines(page_img, min_line_height=min_line_height)
                if line_coords:
                    results.append({
                        "page_path": str(page_path),
                        "line_coordinates": line_coords
                    })
                    print(f" {page_side} page: Found {len(line_coords)} lines.")
                else:
                    print(f" {page_side} page: No lines found.")
    except Exception as e:
        print(f" ERROR processing {file_path}: {e}")
        return []
    print(f" Processing finished: {file_path.name}")
    return results


model_path = "trocr-base-handwritten-ru"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)
processor = TrOCRProcessor.from_pretrained('kazars24/trocr-base-handwritten-ru')
model = VisionEncoderDecoderModel.from_pretrained('kazars24/trocr-base-handwritten-ru').to(device)
model.eval()

def predict_text_from_line_image(line_image: Image.Image):
    print(f"predict_text_from_line_image started")
    if line_image.mode != 'RGB':
        line_image = line_image.convert('RGB')
    inputs = processor(images=line_image, return_tensors="pt").to(device)
    with torch.no_grad():
        generated_ids = model.generate(inputs.pixel_values, max_length=128)
    pred_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print(f"predict_text_from_line_image finished")
    return pred_text

def process_image_with_line_coords(image_path: str, line_coords: list):
    print(f"process_image_with_line_coords started")
    try:
        page_image = Image.open(image_path)
    except IOError:
        print(f"Could not open image file: {image_path}")
        return "", []
    all_line_data = []
    full_text = []
    for coords in line_coords:
        line_image = page_image.crop(coords)
        line_text = predict_text_from_line_image(line_image)
        if line_text:
            full_text.append(line_text)
            all_line_data.append({"text": line_text, "coords": coords})
    print(f"process_image_with_line_coords finished")
    return "\n".join(full_text), all_line_data

def recognize_text_from_file(filepath: str) -> str:
    print(f"recognize_text_from_file started for {filepath}")
    # Create a temporary output folder for preprocessed files
    output_folder = Path("data/preprocessed") / Path(filepath).stem
    output_folder.mkdir(parents=True, exist_ok=True)
    pages_with_coords = process_single_file(Path(filepath), output_folder, file_index=0, min_line_height=50)
    if not pages_with_coords:
        print("No text lines detected for recognition.")
        return ""
    full_texts = []
    for page_data in pages_with_coords:
        page_path = page_data["page_path"]
        line_coords = page_data["line_coordinates"]
        full_text, _ = process_image_with_line_coords(page_path, line_coords)
        full_texts.append(full_text)
    result_text = "\n\n".join(full_texts)
    print(f"recognize_text_from_file finished")
    return result_text

def wer(reference, hypothesis):
    r, h = reference.split(), hypothesis.split()
    import numpy as np
    d = np.zeros([len(r)+1, len(h)+1], dtype=np.uint32)
    for i in range(len(r)+1):
        d[i][0] = i
    for j in range(len(h)+1):
        d[0][j] = j
    for i in range(1, len(r)+1):
        for j in range(1, len(h)+1):
            if r[i-1] == h[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                substitution = d[i-1][j-1] + 1
                insertion    = d[i][j-1] + 1
                deletion     = d[i-1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)
    wer_value = d[len(r)][len(h)] / max(1, len(r))
    return wer_value

