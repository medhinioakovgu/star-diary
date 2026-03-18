"""
train_lora.py – Boilerplate for fine-tuning a causal LM with PEFT/LoRA and
               Weights & Biases experiment tracking.

Usage (once stubs are implemented):
    python train_lora.py --base_model mistralai/Mistral-7B-v0.1 \
                         --data_path data/synthetic_qa.jsonl \
                         --output_dir ../models/paparazzo-lora
"""

import argparse
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def load_base_model(model_name: str):
    """Load a pre-trained causal language model and its tokenizer from
    Hugging Face Hub.

    Args:
        model_name: HuggingFace model identifier (e.g. 'mistralai/Mistral-7B-v0.1').

    Returns:
        A (model, tokenizer) tuple.

    TODO:
        - Use ``transformers.AutoModelForCausalLM.from_pretrained`` with
          ``torch_dtype=torch.float16`` and ``device_map="auto"``.
        - Load the matching tokenizer with ``AutoTokenizer.from_pretrained``.
        - Optionally enable Flash Attention 2 for faster training.
    """
    raise NotImplementedError("load_base_model is not yet implemented.")


def apply_lora(model, r: int = 16, lora_alpha: int = 32, lora_dropout: float = 0.05):
    """Wrap a base model with PEFT/LoRA adapters.

    Args:
        model:        The base HuggingFace model.
        r:            LoRA rank.
        lora_alpha:   LoRA scaling factor.
        lora_dropout: Dropout probability for LoRA layers.

    Returns:
        The PEFT-wrapped model ready for training.

    TODO:
        - Build a ``LoraConfig`` targeting the query and value projection layers.
        - Apply it with ``peft.get_peft_model``.
        - Print the number of trainable parameters.
    """
    raise NotImplementedError("apply_lora is not yet implemented.")


def load_dataset(data_path: str):
    """Load and pre-process the training dataset.

    Args:
        data_path: Path to a JSONL file produced by data_generation.py.

    Returns:
        A HuggingFace ``datasets.Dataset`` object.

    TODO:
        - Use ``datasets.load_dataset("json", data_files=data_path)``.
        - Apply a tokenization map function to convert raw text to input IDs.
    """
    raise NotImplementedError("load_dataset is not yet implemented.")


def init_wandb_run(
    project: str = "star-interview-diary",
    run_name: Optional[str] = None,
    config: Optional[dict] = None,
):
    """Initialise a Weights & Biases run for experiment tracking.

    Args:
        project:  W&B project name.
        run_name: Optional display name for this run.
        config:   Hyperparameter dict to log.

    Returns:
        The active ``wandb.Run`` object.

    TODO:
        - Call ``wandb.init(project=project, name=run_name, config=config)``.
        - Ensure WANDB_API_KEY is set (loaded from .env via python-dotenv).
    """
    raise NotImplementedError("init_wandb_run is not yet implemented.")


def train(
    model,
    tokenizer,
    dataset,
    output_dir: str,
    num_epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-4,
):
    """Run the fine-tuning training loop.

    Args:
        model:         PEFT-wrapped model.
        tokenizer:     Matching tokenizer.
        dataset:       Pre-processed HuggingFace dataset.
        output_dir:    Directory to save checkpoints and the final adapter.
        num_epochs:    Number of training epochs.
        batch_size:    Per-device training batch size.
        learning_rate: Peak learning rate for the AdamW optimiser.

    TODO:
        - Configure ``transformers.TrainingArguments`` with ``report_to="wandb"``.
        - Use ``trl.SFTTrainer`` (or ``transformers.Trainer``) for the training loop.
        - Save the final LoRA adapter with ``model.save_pretrained(output_dir)``.
    """
    raise NotImplementedError("train is not yet implemented.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune a causal LM with LoRA.")
    parser.add_argument("--base_model", default="mistralai/Mistral-7B-v0.1")
    parser.add_argument(
        "--data_path",
        default=os.path.join(os.path.dirname(__file__), "data", "synthetic_qa.jsonl"),
    )
    parser.add_argument(
        "--output_dir",
        default=os.path.join(os.path.dirname(__file__), "..", "models", "paparazzo-lora"),
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    args = parser.parse_args()

    model, tokenizer = load_base_model(args.base_model)
    model = apply_lora(model)
    dataset = load_dataset(args.data_path)
    run = init_wandb_run(config=vars(args))
    train(
        model,
        tokenizer,
        dataset,
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )
