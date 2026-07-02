from pathlib import Path

import fasttext

from tags import ContentCategory

cur_dir = Path(__file__).parent
training_data_dir = cur_dir.parent / "train_model" / "training-data"
category_map = {
    "game": ContentCategory.Game,
    "gore": ContentCategory.Gore,
    "pornography": ContentCategory.Pornography,
    "education": ContentCategory.Education,
}


def _compile_to_train_file(file_path: str | Path, tag: ContentCategory):
    """Bien dich file data "raw" sang file .train cho thu vien fasttext
    vi du file_path = game.txt, tag = ContentCategory.game
    Ham nay se duyet qua tung dong data cua game.txt roi ghi ra file moi la game.train

    # game.txt
    roblox
    minecraft

    # game.train
    __label__Game roblox
    __label__Game minecraft"""

    file_path = Path(file_path)
    output_file = file_path.with_suffix(".train")

    with file_path.open("r", encoding="utf-8") as src:
        raw_data = src.readlines()

    with output_file.open("w", encoding="utf-8") as dst:
        for line in raw_data:
            line = line.strip()
            if not line:
                continue
            _ = dst.write(f"__label__{tag.name} {line}\n")

    return output_file


def _create_main_train_file() -> Path:
    train_files: list[str] = []

    for category_dir in training_data_dir.iterdir():
        if not category_dir.is_dir():
            continue

        tag = category_map.get(category_dir.name.lower())
        if tag is None:
            raise RuntimeError(
                f"Unknown category_dir: {training_data_dir / category_dir.name}"
            )

        for txt_file in category_dir.glob("*.txt"):
            train_file = _compile_to_train_file(txt_file, tag)
            train_files.append(str(train_file))

    if not train_files:
        raise RuntimeError("No training data found.")

    merged_train_file = training_data_dir / "dataset.train"

    with merged_train_file.open("w", encoding="utf-8") as out:
        for train_file in train_files:
            with open(train_file, "r", encoding="utf-8") as src:
                _ = out.write(src.read())

    return merged_train_file


def train_model(
    output_dir: str | Path,
    model_name: str = "fasttext_classifier",
    # Ưu tiên: chính xác > nhanh > nhỏ
    epoch: int = 40,
    lr: float = 0.15,
    dim: int = 50,
    wordNgrams: int = 2,
    minCount: int = 1,
    bucket: int = 100_000,
    minn: int = 3,
    maxn: int = 6,
    loss: str = "softmax",
    thread: int = 4,
    # Nén model
    quantize: bool = True,
    quantize_retrain: bool = True,
):
    """Duoc thiet ke de chap nhan train lau, mat nhieu thoi gian de doi lay chat luong tot
    Muc tieu: cung cap model nhe, nha, hieu suat cao, chinh xac, chap nhan train lau, nong may
    Muc do uu tien: Chinh xac > tiet kiem tai nguyen compute > file size nho"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    merged_train_file = _create_main_train_file()

    model = fasttext.train_supervised(
        input=str(merged_train_file),
        epoch=epoch,
        lr=lr,
        dim=dim,
        wordNgrams=wordNgrams,
        minCount=minCount,
        bucket=bucket,
        minn=minn,
        maxn=maxn,
        loss=loss,
        thread=thread,
    )

    if quantize:
        model.quantize(
            input=str(merged_train_file),
            retrain=quantize_retrain,
        )
        ext = "ftz"
    else:
        ext = "bin"

    config_name = (
        f"{model_name}"
        f"-ep{epoch}"
        f"-lr{lr}"
        f"-dim{dim}"
        f"-ng{wordNgrams}"
        f"-mc{minCount}"
        f"-b{bucket}"
        f"-mn{minn}"
        f"-mx{maxn}"
        f"-{loss}"
    )

    model_output_path = output_dir / f"{config_name}.{ext}"
    model.save_model(str(model_output_path))

    return model_output_path


_ = train_model(
    output_dir=cur_dir.parent / "models",
    model_name="Ritchie",
    quantize_retrain=False,
    quantize=False,
)
