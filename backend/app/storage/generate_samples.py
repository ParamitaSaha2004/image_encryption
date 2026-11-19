import os
import numpy as np
from PIL import Image

def generate_samples():
    samples_dir = os.path.join(os.path.dirname(__file__), 'samples')
    os.makedirs(samples_dir, exist_ok=True)

    # 1. Synthetic Chest X-Ray (512x512 grayscale PNG)
    h, w = 512, 512
    xray = np.zeros((h, w), dtype=np.uint8) + 30
    y_coords, x_coords = np.ogrid[:h, :w]
    spine = np.exp(-((x_coords - 256)**2) / 480.0) * 140
    xray = np.clip(xray + spine, 0, 255).astype(np.uint8)
    left_lung = np.exp(-((x_coords - 160)**2 / 2400.0 + (y_coords - 240)**2 / 8000.0)) * 60
    right_lung = np.exp(-((x_coords - 352)**2 / 2400.0 + (y_coords - 240)**2 / 8000.0)) * 60
    xray = np.clip(xray - left_lung - right_lung + 50, 20, 240).astype(np.uint8)
    heart = np.exp(-((x_coords - 290)**2 / 3200.0 + (y_coords - 300)**2 / 4000.0)) * 90
    xray = np.clip(xray + heart, 0, 255).astype(np.uint8)
    Image.fromarray(xray, mode='L').save(os.path.join(samples_dir, 'synthetic_chest_xray.png'))

    # 2. Synthetic Brain MRI (256x256 grayscale PNG)
    h2, w2 = 256, 256
    y_coords2, x_coords2 = np.ogrid[:h2, :w2]
    mri = np.zeros((h2, w2), dtype=np.uint8) + 10
    head_ellipse = ((x_coords2 - 128)**2 / 7000.0 + (y_coords2 - 128)**2 / 9000.0) <= 1.0
    brain_tissue = ((x_coords2 - 128)**2 / 5500.0 + (y_coords2 - 128)**2 / 7500.0) <= 1.0
    mri[head_ellipse] = 80
    mri[brain_tissue] = 130
    ventricle1 = np.exp(-((x_coords2 - 115)**2 / 80.0 + (y_coords2 - 125)**2 / 400.0)) * 100
    ventricle2 = np.exp(-((x_coords2 - 141)**2 / 80.0 + (y_coords2 - 125)**2 / 400.0)) * 100
    mri = np.clip(mri - ventricle1 - ventricle2, 10, 255).astype(np.uint8)
    Image.fromarray(mri, mode='L').save(os.path.join(samples_dir, 'synthetic_brain_mri.png'))

    # 3. Histology Microscopy Cell Stain (256x256 RGB BMP)
    histo = np.ones((h2, w2, 3), dtype=np.uint8) * 235
    histo[:, :, 0] = 230
    histo[:, :, 1] = 180
    histo[:, :, 2] = 210
    rng = np.random.default_rng(42)
    for _ in range(40):
        cx, cy = rng.integers(20, 236, size=2)
        radius = rng.integers(6, 14)
        dist = (x_coords2 - cx)**2 + (y_coords2 - cy)**2
        mask = dist <= radius**2
        histo[mask, 0] = 90
        histo[mask, 1] = 30
        histo[mask, 2] = 130
    Image.fromarray(histo, mode='RGB').save(os.path.join(samples_dir, 'sample_histology.bmp'))

    print('Successfully generated synthetic medical samples:')
    for item in os.listdir(samples_dir):
        print(f" - {item}: {os.path.getsize(os.path.join(samples_dir, item))} bytes")

if __name__ == '__main__':
    generate_samples()
