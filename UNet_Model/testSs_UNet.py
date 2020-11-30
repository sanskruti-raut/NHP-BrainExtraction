#!/usr/bin/env python
import torch
import torch.nn as nn
import numpy as np
import scipy.ndimage as snd
from torch.autograd import Variable
from dataset import VolumeDataset, BlockDataset
from torch.utils.data import DataLoader
from model import MultiSliceBcUNet, MultiSliceSsUNet, MultiSliceModel, UNet2d
from function import predict_volumes
import os, sys, pickle
import nibabel as nib
import argparse

if __name__=='__main__':
    NoneType=type(None)
    # Argument
    parser = argparse.ArgumentParser(description='Testing Model', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    optional=parser._action_groups.pop()
    required=parser.add_argument_group('required arguments')
    # Required Option
    required.add_argument('-tet1w', '--test_t1w', type=str, required=True, help='Test T1w Directory')
    required.add_argument('-temsk', '--test_msk', type=str, required=True, help='Test Mask Directory')
    required.add_argument('-out', '--out_dir', type=str, required=True, help='Output Directory')
    required.add_argument('-model', '--test_model', type=str, required=True, help='Test Model')
    # Optional Option
    optional.add_argument('-slice', '--input_slice', type=int, default=3, help='Number of Slice for Model Input')
    optional.add_argument('-conv', '--conv_block', type=int, default=5, help='Number of UNet Block')
    optional.add_argument('-kernel', '--kernel_root', type=int, default=16, help='Number of the Root of Kernel')
    optional.add_argument('-rescale', '--rescale_dim', type=int, default=256, help='Number of the Root of Kernel')
    parser._action_groups.append(optional)
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()

    print("===================================Testing Model====================================")

    if not os.path.exists(args.test_msk) or not os.path.exists(args.test_t1w):
        print("Invalid test directory, please check again!")
        sys.exit(2)

    if not os.path.exists(args.test_model):
        print("Invalid test model, please check again!")
        sys.exit(2)

    train_model=UNet2d(dim_in=args.input_slice, num_conv_block=args.conv_block, kernel_root=args.kernel_root)
    checkpoint=torch.load(args.test_model, map_location={'cuda:0':'cpu'})
    train_model.load_state_dict(checkpoint['state_dict'])

    model=nn.Sequential(train_model, nn.Softmax2d())
    dice_dict=predict_volumes(model, rimg_in=None, cimg_in=args.test_t1w, bmsk_in=args.test_msk, 
        rescale_dim=args.rescale_dim, save_nii=True, nii_outdir=args.out_dir, save_dice=True)
    dice_array=np.array([v for v in dice_dict.values()])
    print("\t%.4f +/- %.4f" % (dice_array.mean(), dice_array.std()))
    with open(os.path.join(args.out_dir, "Dice.pkl"), 'wb') as f:
        pickle.dump(dice_dict, f)
