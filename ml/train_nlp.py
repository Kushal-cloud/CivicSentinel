"""
Transformer-based NLP fine-tuning helper for CivicSentinel.

This script is intentionally generic because civic-letter datasets vary widely.

Recommended approach:
- Collect training pairs: (structured complaint inputs -> final complaint letter)
- Store as JSONL with fields:
    - "prompt": the model prompt (e.g., issue/location/severity/tone)
    - "target": the desired letter text

Example:
  python ml/train_nlp.py --train data/train.jsonl --model google/flan-t5-small --out ./runs/nlp
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True, help="Path to JSONL training data")
    parser.add_argument("--model", default="google/flan-t5-small", help="Base model name or local path")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--max_source_length", type=int, default=512)
    parser.add_argument("--max_target_length", type=int, default=1024)
    args = parser.parse_args()

    try:
        from transformers import (
            AutoModelForSeq2SeqLM,
            AutoTokenizer,
            DataCollatorForSeq2Seq,
            Seq2SeqTrainer,
            Seq2SeqTrainingArguments,
        )  # type: ignore
    except Exception as e:
        raise SystemExit("Missing transformers. Install backend/requirements-ml.txt") from e

    train_path = Path(args.train)
    if not train_path.exists():
        raise SystemExit(f"Training file not found: {train_path}")

    examples = []
    with train_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            examples.append({"prompt": obj["prompt"], "target": obj["target"]})

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model)

    def tokenize_batch(batch):
        inputs = tokenizer(
            [x["prompt"] for x in batch],
            max_length=args.max_source_length,
            truncation=True,
            padding="max_length",
        )
        targets = tokenizer(
            [x["target"] for x in batch],
            max_length=args.max_target_length,
            truncation=True,
            padding="max_length",
        )
        inputs["labels"] = targets["input_ids"]
        return inputs

    # Minimal dataset wrapper (avoids dependency on `datasets`).
    class ListDataset:
        def __len__(self):
            return len(examples)

        def __getitem__(self, idx):
            # Trainer expects dict-like with tokenized fields; keep as raw and tokenize via collator.
            return examples[idx]

    train_ds = ListDataset()

    class Collator(DataCollatorForSeq2Seq):
        def __call__(self, features):
            tokenized = tokenize_batch(features)
            return tokenized

    collator = Collator(tokenizer=tokenizer, model=model)

    training_args = Seq2SeqTrainingArguments(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=5e-5,
        warmup_steps=100,
        logging_steps=50,
        save_steps=200,
        save_total_limit=2,
        fp16=False,
        report_to="none",
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        data_collator=collator,
        tokenizer=tokenizer,
    )

    trainer.train()
    trainer.save_model(args.out)


if __name__ == "__main__":
    main()

