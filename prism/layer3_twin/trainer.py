import pytorch_lightning as pl
import argparse
from pytorch_lightning.loggers import WandbLogger
from layer3_twin.organ_twins.metabolic_twin import MetabolicTwin, MetabolicDataModule
from layer3_twin.organ_twins.cardiopulmonary_twin import CardiopulmonaryTwin, CardiopulmonaryDataModule
from layer3_twin.organ_twins.infectious_twin import InfectiousTwin, InfectiousDataModule

def get_twin_and_data(twin_name):
    if twin_name == 'metabolic':
        return MetabolicTwin(), MetabolicDataModule()
    elif twin_name == 'cardiopulmonary':
        return CardiopulmonaryTwin(), CardiopulmonaryDataModule()
    elif twin_name == 'infectious':
        return InfectiousTwin(), InfectiousDataModule()
    else:
        raise ValueError(f"Unknown twin: {twin_name}")

def train_twin(args):
    model, datamodule = get_twin_and_data(args.twin)
    
    # Initialize W&B logger if enabled
    logger = None
    if args.use_wandb:
        logger = WandbLogger(project="prism-digital-twin", name=f"{args.twin}_training")
        
    trainer = pl.Trainer(
        max_epochs=args.epochs,
        logger=logger,
        accelerator='auto',
        devices=1
    )
    
    trainer.fit(model, datamodule=datamodule)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--twin", type=str, required=True, choices=['metabolic', 'cardiopulmonary', 'infectious'])
    parser.add_argument("--data-dir", type=str, default="prism/data")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--use-wandb", action="store_true", help="Enable W&B logging")
    
    args = parser.parse_args()
    train_twin(args)
