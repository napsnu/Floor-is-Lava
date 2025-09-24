import argparse
import os
import cv2

ARUCO_DICT_NAME = "DICT_4X4_50"


def get_aruco_dictionary():
    if not hasattr(cv2, 'aruco'):
        raise RuntimeError("OpenCV ArUco module not found. Install opencv-contrib-python.")
    aruco = cv2.aruco
    if not hasattr(aruco, ARUCO_DICT_NAME):
        raise RuntimeError(f"ArUco dict {ARUCO_DICT_NAME} is not available in cv2.aruco")
    return getattr(aruco, ARUCO_DICT_NAME)


def generate_marker(marker_id: int, size_px: int = 600):
    aruco = cv2.aruco
    dictionary = aruco.getPredefinedDictionary(get_aruco_dictionary())
    img = aruco.generateImageMarker(dictionary, marker_id, size_px)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img


def save_marker_image(img, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, img)


def main():
    parser = argparse.ArgumentParser(description="Generate ArUco markers IDs 0-3")
    parser.add_argument('--out', type=str, default='markers', help='Output directory')
    parser.add_argument('--size', type=int, default=600, help='Marker size in pixels')
    args = parser.parse_args()

    for marker_id in [0, 1, 2, 3]:
        img = generate_marker(marker_id, args.size)
        out_path = os.path.join(args.out, f"marker_{marker_id}.png")
        save_marker_image(img, out_path)
        print(f"Saved {out_path}")


if __name__ == '__main__':
    main() 