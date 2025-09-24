import json
import os
import numpy as np
from mapping import PixelToGridMapper


def test_pixel_to_grid_cell_out_of_bounds(tmp_path):
    H = np.eye(3)
    np.save(tmp_path / 'homography.npy', H)
    with open(tmp_path / 'grid_config.json', 'w') as f:
        json.dump({'rows': 8, 'cols': 8}, f)

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        mapper = PixelToGridMapper('homography.npy', 'grid_config.json')
        # pixel (0,0) maps to grid (0,0)
        r, c, oob = mapper.pixel_to_grid_cell(0, 0)
        assert (r, c) == (0, 0)
        assert oob is False
        # pixel far maps to far grid -> floor -> oob
        r, c, oob = mapper.pixel_to_grid_cell(10000, 10000)
        assert oob is True
    finally:
        os.chdir(cwd) 