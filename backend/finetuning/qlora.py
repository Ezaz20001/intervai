import json
from typing import List, Dict, Any, Optional

from backend import config


class QLoRAPipeline:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.trainer = None

    def prepare_dataset(self, jsonl_path: str) -> List[Dict[str, str]]:
        try:
            from datasets import load_dataset
        except ImportError:
            return self._prepare_dataset_manual(jsonl_path)

        dataset = load_dataset("json", data_files=jsonl_path, split="train")

        def format_pair(example):
            if example["label"] == "good":
                prefix = "Rate this interview answer as GOOD. Question: "
                completion = f"{example['answer']}\n\nScore: {example['score']}/10"
            else:
                prefix = "Rate this interview answer as BAD. Question: "
                completion = f"{example['answer']}\n\nScore: {example['score']}/10"
            return {
                "prompt": prefix + example["question"],
                "completion": completion,
            }

        formatted = dataset.map(format_pair, remove_columns=dataset.column_names)
        return formatted

    def _prepare_dataset_manual(self, jsonl_path: str) -> List[Dict[str, str]]:
        pairs = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line.strip())
                if item["label"] == "good":
                    prompt = "Rate this interview answer as GOOD. Question: " + item["question"]
                    completion = f"{item['answer']}\n\nScore: {item['score']}/10"
                else:
                    prompt = "Rate this interview answer as BAD. Question: " + item["question"]
                    completion = f"{item['answer']}\n\nScore: {item['score']}/10"
                pairs.append({"prompt": prompt, "completion": completion})
        return pairs

    def setup_peft_config(self):
        try:
            from peft import LoraConfig, get_peft_model, TaskType
        except ImportError:
            raise ImportError(
                "peft is required for QLoRA. Install with: pip install peft"
            )

        return LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
        )

    def train(self, output_dir: str = "data/finetuned_model"):
        try:
            import torch
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                BitsAndBytesConfig,
                TrainingArguments,
                Trainer,
                DataCollatorForLanguageModeling,
            )
            from peft import get_peft_model
            from datasets import Dataset
        except ImportError as e:
            raise ImportError(
                f"Required packages not available: {e}. "
                "Install with: pip install transformers torch peft datasets bitsandbytes"
            ) from e

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )

        model_name = config.LOCAL_LLM_MODEL
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
        )
        self.model.gradient_checkpointing_enable()

        peft_config = self.setup_peft_config()
        self.model = get_peft_model(self.model, peft_config)

        dataset = self._prepare_dataset_manual(
            config.DATABASE_PATH.rsplit("/", 1)[0] + "/finetuning_data.jsonl"
        )

        def tokenize_fn(examples):
            return self.tokenizer(
                examples["prompt"],
                truncation=True,
                max_length=512,
                padding="max_length",
            )

        if isinstance(dataset, list):
            hf_dataset = Dataset.from_list(dataset)
        else:
            hf_dataset = dataset
        tokenized = hf_dataset.map(tokenize_fn, batched=True)

        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=3,
            per_device_train_batch_size=4,
            learning_rate=2e-4,
            warmup_steps=10,
            logging_steps=10,
            save_strategy="epoch",
            gradient_checkpointing=True,
            fp16=True,
            optim="paged_adamw_8bit",
            report_to="none",
        )

        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )

        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized,
            data_collator=data_collator,
        )

        self.trainer.train()
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)

        return output_dir

    def evaluate(self, test_data: List[Dict]) -> Dict[str, Any]:
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not trained or loaded. Call train() first.")

        correct = 0
        total = 0
        predictions = []

        for item in test_data:
            prompt = "Rate this interview answer as GOOD or BAD. Question: " + item["question"]
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

            try:
                import torch
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                with torch.no_grad():
                    outputs = self.model.generate(**inputs, max_new_tokens=20)
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            except Exception:
                response = ""

            predicted_label = "good" if "GOOD" in response.upper()[-20:] else "bad"
            actual_label = item["label"]

            if predicted_label == actual_label:
                correct += 1
            total += 1

            predictions.append({
                "question": item["question"],
                "predicted": predicted_label,
                "actual": actual_label,
                "correct": predicted_label == actual_label,
            })

        accuracy = correct / total if total > 0 else 0.0

        return {
            "accuracy": round(accuracy, 4),
            "correct": correct,
            "total": total,
            "predictions": predictions,
        }
