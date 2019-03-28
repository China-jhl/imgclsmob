import os
import numpy as np
import mxnet as mx
from PIL import Image
from .seg_dataset import SegDataset


class ADE20KSegDataset(SegDataset):
    """
    ADE20K semantic segmentation dataset.

    Parameters
    ----------
    root : string
        Path to ADE20K folder.
    mode: string, default 'train'
        'train', 'val', 'test', or 'demo'.
    transform : callable, optional
        A function that transforms the image.
    """
    def __init__(self,
                 root,
                 mode="train",
                 transform=None,
                 **kwargs):
        super(ADE20KSegDataset, self).__init__(
            root=root,
            mode=mode,
            transform=transform,
            **kwargs)
        self.classes = 151

        base_dir_path = os.path.join(root, "ADEChallengeData2016")
        assert os.path.exists(base_dir_path), "Please prepare dataset"

        image_dir_path = os.path.join(base_dir_path, "images")
        mask_dir_path = os.path.join(base_dir_path, "annotations")

        mode_dir_name = "training" if mode == "train" else "validation"
        image_dir_path = os.path.join(image_dir_path, mode_dir_name)
        mask_dir_path = os.path.join(mask_dir_path, mode_dir_name)

        self.images = []
        self.masks = []
        for image_file_name in os.listdir(image_dir_path):
            image_file_stem, _ = os.path.splitext(image_file_name)
            if image_file_name.endswith(".jpg"):
                image_file_path = os.path.join(image_dir_path, image_file_name)
                mask_file_name = image_file_stem + ".png"
                mask_file_path = os.path.join(mask_dir_path, mask_file_name)
                if os.path.isfile(mask_file_path):
                    self.images.append(image_file_path)
                    self.masks.append(mask_file_path)
                else:
                    print("Cannot find the mask: {}".format(mask_file_path))

        assert (len(self.images) == len(self.masks))
        if len(self.images) == 0:
            raise RuntimeError("Found 0 images in subfolders of: {}\n".format(base_dir_path))

    def __getitem__(self, index):
        image = Image.open(self.images[index]).convert("RGB")
        # image = mx.image.imread(self.images[index])
        if self.mode == "demo":
            image = self._img_transform(image)
            if self.transform is not None:
                image = self.transform(image)
            return image, os.path.basename(self.images[index])
        mask = Image.open(self.masks[index])
        # mask = mx.image.imread(self.masks[index])

        if self.mode == "train":
            image, mask = self._sync_transform(image, mask)
        elif self.mode == "val":
            image, mask = self._val_sync_transform(image, mask)
        else:
            assert (self.mode == "test")
            image = self._img_transform(image)
            mask = self._mask_transform(mask)

        if self.transform is not None:
            image = self.transform(image)
        return image, mask

    vague_idx = -1
    use_vague = False
    background_idx = 0
    ignore_bg = True

    @staticmethod
    def _mask_transform(mask):
        np_mask = np.array(mask).astype(np.int32)
        # np_mask[np_mask == 0] = ADE20KSegDataset.vague_idx
        # np_mask -= 1
        return mx.nd.array(np_mask, mx.cpu())

    def __len__(self):
        return len(self.images)