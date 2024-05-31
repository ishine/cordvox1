import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import lightning as L

from module.cordvox import Cordvox
from module.utils.dataset import VocoderDataModule
from module.utils.config import load_json_file

class SaveCheckpoint(L.Callback):
    def __init__(self, models_dir, interval=200):
        super().__init__()
        self.models_dir = Path(models_dir)
        self.interval = interval
        if not self.models_dir.exists():
            self.models_dir.mkdir()

    def on_train_batch_end(self, trainer, pl_module, outputs, batch, batch_idx):
        if batch_idx % self.interval == 0:
            ckpt_path = self.models_dir / "model.ckpt"
            trainer.save_checkpoint(ckpt_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, default="config/v3_24k.json")
    parser.add_argument("-da", "--discriminator-active", type=bool, default=False)
    args = parser.parse_args()

    config = load_json_file(args.config)
    model_path = Path(config['save']['models_dir']) / "model.ckpt"
    cb_save_checkpoint = SaveCheckpoint(config['save']['models_dir'], interval=config['save']['interval'])
    trainer = L.Trainer(**config["trainer"], callbacks=[cb_save_checkpoint])

    if model_path.exists():
        print(f"loading model from {model_path}")
        model = Cordvox.load_from_checkpoint(model_path)
    else:
        model = Cordvox(config["model"])

    model.discriminator_active = args.discriminator_active
    dm = VocoderDataModule(**config['data_module'])
    trainer.fit(model, dm)
