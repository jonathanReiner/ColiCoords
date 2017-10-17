import tifffile
import os
from colicoords.preprocess import process_cell
from colicoords.fileIO import save

fl_img = tifffile.imread('test_data/flu1.tif')
binary_img = tifffile.imread('test_data/binary1.tif')


cell = process_cell(rotate='binary', binary_img=binary_img, flu_data={'514': fl_img})
cell.optimize(method='binary')

#
with tifffile.TiffFile(r'cell.tif') as tif1:
    arr = tif1.asarray()
#     print(tif)
    print('cell.tif')
#     print(tif.info())