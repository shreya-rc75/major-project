import os
from pathlib import Path
from typing import List, Dict, Any
import torch
from torch.utils.data import DataLoader
from sklearn.model_selection import StratifiedKFold
from torch import nn, optim
from torch.cuda.amp import GradScaler, autocast
from torch.utils.tensorboard import SummaryWriter
from app.ai.data.dataset import PapSmearDataset
from app.ai.data.transforms import train_transforms, val_transforms
from app.ai.model.model import EfficientNetB3Wrapper
from app.ai.training.utils import compute_metrics
import time
import json


class Trainer:
    def __init__(
        self,
        records: List[tuple],
        labels: List[int],
        output_dir: str = "./models",
        num_classes: int = 2,
        folds: int = 5,
        epochs: int = 30,
        batch_size: int = 16,
        lr: float = 1e-4,
        patience: int = 5,
        device: str = None,
    ) -> None:
        self.records = records
        self.labels = labels
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.num_classes = num_classes
        self.folds = folds
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.patience = patience
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def _build_model(self):
        model = EfficientNetB3Wrapper(num_classes=self.num_classes, pretrained=True)
        return model.to(self.device)

    def train(self):
        skf = StratifiedKFold(n_splits=self.folds, shuffle=True, random_state=42)
        records_arr = self.records
        y = self.labels
        for fold, (train_idx, val_idx) in enumerate(skf.split(records_arr, y)):
            print(f"Starting fold {fold + 1}/{self.folds}")
            train_records = [records_arr[i] for i in train_idx]
            val_records = [records_arr[i] for i in val_idx]

            train_ds = PapSmearDataset(train_records, transforms=train_transforms(), return_path=False)
            val_ds = PapSmearDataset(val_records, transforms=val_transforms(), return_path=False)

            train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True, num_workers=4, pin_memory=True)
            val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False, num_workers=4, pin_memory=True)

            model = self._build_model()
            criterion = nn.CrossEntropyLoss()
            optimizer = optim.AdamW(model.parameters(), lr=self.lr)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)
            scaler = GradScaler()

            writer = SummaryWriter(log_dir=str(self.output_dir / f"runs/fold_{fold}"))
            best_val_loss = float("inf")
            epochs_no_improve = 0
            best_path = self.output_dir / f"efficientnet_b3_fold{fold}.pth"

            for epoch in range(1, self.epochs + 1):
                t0 = time.time()
                model.train()
                running_loss = 0.0
                for batch in train_loader:
                    imgs, labels = batch
                    imgs = imgs.to(self.device)
                    labels = labels.to(self.device)
                    optimizer.zero_grad()
                    with autocast():
                        logits = model(imgs)
                        loss = criterion(logits, labels)
                    scaler.scale(loss).backward()
                    scaler.step(optimizer)
                    scaler.update()
                    running_loss += loss.item() * imgs.size(0)

                epoch_loss = running_loss / len(train_loader.dataset)

                # validation
                model.eval()
                val_loss = 0.0
                all_preds = []
                all_labels = []
                with torch.no_grad():
                    for batch in val_loader:
                        imgs, labels = batch
                        imgs = imgs.to(self.device)
                        labels = labels.to(self.device)
                        logits = model(imgs)
                        loss = criterion(logits, labels)
                        val_loss += loss.item() * imgs.size(0)
                        preds = torch.argmax(logits, dim=1).cpu().numpy()
                        all_preds.extend(preds.tolist())
                        all_labels.extend(labels.cpu().numpy().tolist())
                val_loss = val_loss / len(val_loader.dataset)

                metrics = compute_metrics(all_labels, all_preds)
                writer.add_scalar("train/loss", epoch_loss, epoch)
                writer.add_scalar("val/loss", val_loss, epoch)
                writer.add_scalar("val/accuracy", metrics["accuracy"], epoch)
                writer.add_scalar("val/f1", metrics["f1"] if "f1" in metrics else 0.0, epoch)

                print(f"Fold {fold} Epoch {epoch}: train_loss={epoch_loss:.4f} val_loss={val_loss:.4f} acc={metrics['accuracy']:.4f} f1={metrics.get('f1',0):.4f}")

                scheduler.step(val_loss)

                # early stopping
                if val_loss < best_val_loss - 1e-6:
                    best_val_loss = val_loss
                    epochs_no_improve = 0
                    # save checkpoint
                    torch.save(model.state_dict(), str(best_path))
                else:
                    epochs_no_improve += 1
                    if epochs_no_improve >= self.patience:
                        print(f"Early stopping at epoch {epoch} for fold {fold}")
                        break

            writer.close()

        # After training, write a manifest
        manifest = {"folds": self.folds, "model_files": [str(p.name) for p in Path(self.output_dir).glob("*.pth")]}
        with open(self.output_dir / "manifest.json", "w") as fh:
            json.dump(manifest, fh)

        print("Training complete")
