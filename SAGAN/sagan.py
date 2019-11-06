import os
import time
import datetime
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torchvision.utils import save_image

from losses import *
from layers import *
from generator import Generator
from discriminator import Discriminator


class SAGAN():
    def __init__(self, data_loader, configs):

        # Data Loader
        self.data_loader = data_loader

        # model settings & hyperparams
        self.total_steps = configs.total_steps
        self.batch_size = configs.batch_size
        self.imsize = configs.imsize
        self.nz = configs.nz
        self.ngf = configs.ngf
        self.ndf = configs.ndf
        self.g_lr = configs.g_lr
        self.d_lr = configs.d_lr
        self.beta1 = configs.beta1
        self.beta2 = configs.beta2

        self.build_model()

    def build_model(self):
        # initialize Generator and Discriminator
        self.G = Generator(self.batch_size, self.imsize, self.nz, self.ngf).cuda()
        self.D = Discriminator(self.batch_size, self.imsize, self.ndf).cuda()

        # optimizers
        self.g_opt = optim.Adam(filter(
            lambda p: p.requires_grad, self.G.parameters()), self.g_lr, [self.beta1, self.beta2])
        self.d_opt = optim.Adam(filter(
            lambda p: p.requires_grad, self.D.parameters()), self.d_lr, [self.beta1, self.beta2])

        print(self.G)
        print(self.D)

    def train(self):
        data_iter = iter(self.data_loader)
        step_per_epoch = len(self.data_loader)
        
        # fixed z for sampling generator images
        fixed_z = tensor2var(torch.randn(self.batch_size, self.nz))

        start_time = time.time()
        for step in range(self.total_steps):
            # train layers
            self.D.train()
            self.G.train()

            # real and fake samples
            real_images, _ = next(data_iter)
            real_images = tensor2var(real_images)
            z = tensor2var(torch.randn(real_images.size(0), self.nz))
            fake_images, g_beta1, g_beta2 = self.G(z)

            # compute hinge loss for discriminator
            d_real, dr_beta1, dr_beta2 = self.D(real_images)
            d_fake, df_beta1, df_beta2 = self.D(real_images)

            d_loss_real, d_loss_fake = loss_hinge_dis(d_real, d_fake)
            d_loss = d_loss_real + d_loss_fake

            # compute hinge loss for generator
            g_loss_fake = loss_hinge_gen(d_fake)

            # backward + optimize
            self.d_optimizer.zero_grad()
            self.g_optimizer.zero_grad()
            d_loss.backward()
            self.d_opt.step()
            g_loss_fake.backward()
            self.g_opt.step()

            # sample images
            if (step+1) % 5 == 0:
                elapsed = time.time() - start_time
                elapsed = str(datetime.timedelta(seconds=elapsed))
                print("Elapsed [{}], G_step [{}/{}], D_step[{}/{}], d_out_real: {:.4f}, "
                      " ave_gamma_l3: {:.4f}, ave_gamma_l4: {:.4f}".
                      format(elapsed, step + 1, self.total_step, (step + 1),
                             self.total_step , d_loss_real.data[0],
                             self.G.attn1.gamma.mean().data[0], self.G.attn2.gamma.mean().data[0] ))

            if (step+1) % 10 == 0:
                fake_images,_,_ = self.G(fixed_z)
                fake_images = denorm(fake_images.data)
                save_image(fake_images, "./samples/")










